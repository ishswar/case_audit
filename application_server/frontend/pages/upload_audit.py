import streamlit as st
import requests
import time
import pandas as pd
import json
import os
import io
import base64
from urllib.parse import urljoin

# API endpoint
API_URL = "http://localhost:8000"

def upload_pdf(pdf_file):
    if pdf_file is None:
        return None
    
    try:
        files = {"file": (pdf_file.name, pdf_file, "application/pdf")}
        response = requests.post(urljoin(API_URL, "upload/"), files=files)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result["job_id"]
            st.session_state.jobs[job_id] = {
                "status": "pending",
                "filename": pdf_file.name,
                "upload_time": time.time()
            }
            st.session_state.current_job_id = job_id
            # Show status area when we start processing
            st.session_state.status_visible = True
            return job_id
        else:
            st.error(f"Error uploading file: {response.text}")
            return None
    
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

def check_job_status(job_id):
    try:
        response = requests.get(urljoin(API_URL, f"status/{job_id}"))
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Could not get status for job {job_id}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

def get_report(job_id):
    try:
        response = requests.get(urljoin(API_URL, f"report/{job_id}"))
        if response.status_code == 200:
            return response.text
        else:
            st.warning(f"Could not get report for job {job_id}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

def delete_report(case_number):
    try:
        response = requests.delete(urljoin(API_URL, f"report/{case_number}"))
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                # Remove any jobs related to this case from session state
                for job_id in list(st.session_state.jobs.keys()):
                    job = st.session_state.jobs[job_id]
                    if job.get("case_number") == case_number:
                        del st.session_state.jobs[job_id]
                return True, result["message"]
            else:
                return False, result["message"]
        else:
            return False, f"Server error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Error connecting to server: {str(e)}"

def reset_view():
    st.session_state.showing_report = False
    st.session_state.current_job_id = None
    st.session_state.status_visible = False

# Function to hide report when a new PDF is selected
def hide_shown_report():
    st.session_state.showing_report = False
    st.session_state.current_job_id = None
    st.session_state.status_visible = False

def main():
    st.header("Upload TIBCO Case PDF")
    
    col1, col2 = st.columns([4, 6])

    with col1:
        # File uploader with callback to hide report when a new file is selected
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", on_change=hide_shown_report)
    
        if st.button("Process PDF", disabled=uploaded_file is None):
            with st.spinner("Uploading PDF..."):
                # Hide any previously shown report when processing a new PDF
                st.session_state.showing_report = False
                job_id = upload_pdf(uploaded_file)
                if job_id:
                    st.success(f"PDF uploaded successfully! Processing...")
                    
                    # Check if this is an existing report
                    if job_id.startswith("existing_") or job_id.startswith("reused_"):
                        # Automatically show the report for existing/reused reports
                        st.session_state.showing_report = True 
                        st.session_state.status_visible = False
                    else:
                        # Poll for completion status a few times
                        max_retries = 5
                        for _ in range(max_retries):
                            time.sleep(1)  # Short pause between status checks
                            status_info = check_job_status(job_id)
                            if status_info and status_info.get("status") == "completed":
                                st.session_state.showing_report = True
                                st.session_state.status_visible = False
                                break
        
        # Status area - only show when processing is happening
        if st.session_state.current_job_id and st.session_state.status_visible:
            job_id = st.session_state.current_job_id
            
            status_placeholder = st.empty()
            status_placeholder.subheader("Processing Status")
            status_container = st.container()
            
            # Check if this is an "existing_" or "reused_" job (pre-existing report)
            if job_id.startswith("existing_") or job_id.startswith("reused_"):
                if job_id.startswith("reused_"):
                    with status_container:
                        st.success("Existing report found for this case")
                else:
                    with status_container:
                        st.success("Report is available")
                
                # Automatically show the report and hide status after a short delay
                st.session_state.showing_report = True
                st.session_state.status_visible = False
            else:
                # Check status periodically for processing jobs
                status_info = check_job_status(job_id)
                
                if status_info:
                    status = status_info["status"]
                    # Update or create the job in session state
                    if job_id not in st.session_state.jobs:
                        st.session_state.jobs[job_id] = {}
                    st.session_state.jobs[job_id].update(status_info)
                    
                    if status == "pending":
                        with status_container:
                            st.info("Job is queued for processing...")
                    elif status == "processing":
                        with status_container:
                            st.info("Processing your PDF...")
                    elif status == "completed":
                        with status_container:
                            st.success("Analysis complete!")
                        # Automatically show the report and hide status
                        st.session_state.showing_report = True
                        st.session_state.status_visible = False
                    elif status == "failed":
                        with status_container:
                            st.error(f"Processing failed: {status_info.get('error', 'Unknown error')}")
                else:
                    # Job not found - check if it's in the reports list
                    reports = list_reports()
                    
                    # Find any report that might match the job we're looking for
                    for report_id, report_info in reports.items():
                        # If we have case_number in our job info, check if it appears in reports
                        if job_id in st.session_state.jobs and "case_number" in st.session_state.jobs[job_id]:
                            job_case_number = st.session_state.jobs[job_id]["case_number"]
                            if job_case_number == report_info.get("case_number"):
                                with status_container:
                                    st.success("Analysis complete!")
                                # Update our job info with the report info
                                st.session_state.jobs[job_id].update(report_info)
                                # Automatically show the report and hide status
                                st.session_state.showing_report = True
                                st.session_state.status_visible = False
                                break
                    else:
                        # No matching report found - could be truly gone
                        with status_container:
                            st.warning("Job status unknown")
                            if st.button("Reset"):
                                reset_view()

    # Display the report if needed
    if st.session_state.showing_report and st.session_state.current_job_id:
        job_id = st.session_state.current_job_id
        
        # For reused job IDs, we might need special handling
        if job_id.startswith("reused_") and job_id not in st.session_state.jobs:
            # Try to extract the case number
            parts = job_id.split("_")
            if len(parts) > 1:
                case_number = parts[1]
                st.info(f"Trying to retrieve existing report for case {case_number}...")
                
                # Look for this case number in the reports list
                reports = list_reports()
                for report_id, info in reports.items():
                    if info.get("case_number") == case_number:
                        # Found a matching report - use its info
                        st.session_state.current_job_id = report_id
                        job_id = report_id
                        break
        
        # Make sure the job_id is in session state (for existing reports)
        if job_id not in st.session_state.jobs:
            # Fetch the info from the server
            status_info = check_job_status(job_id)
            if status_info:
                st.session_state.jobs[job_id] = status_info
        
        # Get the report content
        report_content = get_report(job_id)
        
        if report_content:
            st.markdown(report_content)
            
            # Download button for the report
            b64 = base64.b64encode(report_content.encode()).decode()
            
            # Safely get case_id from session state or API
            if job_id in st.session_state.jobs:
                case_id = st.session_state.jobs[job_id].get("case_number", "unknown")
            else:
                # Try to extract from job_id for reused/existing jobs
                if job_id.startswith("reused_") or job_id.startswith("existing_"):
                    parts = job_id.split("_")
                    if len(parts) > 1:
                        case_id = parts[1]
                    else:
                        case_id = "unknown"
                else:
                    # Get from URL if possible
                    job_info = check_job_status(job_id)
                    case_id = job_info.get("case_number", "unknown") if job_info else "unknown"
                
            filename = f"case_{case_id}_audit.md"
            href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download Report</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            # Add buttons for navigation and deletion
            back_col, delete_col = st.columns([3, 2])
            
            with back_col:
                if st.button("Back to Reports"):
                    reset_view()
            
            with delete_col:
                # Add a delete button for the current report
                if st.button("Delete This Report", type="secondary", key="delete_from_upload"):
                    if st.session_state.get("confirm_delete") == case_id:
                        # User has confirmed, proceed with deletion
                        success, message = delete_report(case_id)
                        if success:
                            st.success(message)
                            reset_view()
                            # Reset confirmation state
                            st.session_state.pop("confirm_delete", None)
                            # Refresh the page to show updated reports
                            st.rerun()
                        else:
                            st.error(message)
                            # Reset confirmation state
                            st.session_state.pop("confirm_delete", None)
                    else:
                        # Ask for confirmation
                        st.session_state.confirm_delete = case_id
                        st.warning(f"Are you sure you want to delete this report? Click 'Delete This Report' again to confirm.")
                        
        else:
            st.error("Could not load report content.")
            
            # Offer to go back to the report list
            if st.button("Back to Reports"):
                reset_view()

# Function imported from main app
def list_reports():
    try:
        response = requests.get(urljoin(API_URL, "reports/"))
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Could not get list of reports: {response.text}")
            return {}
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return {}

if __name__ == "__main__":
    main() 