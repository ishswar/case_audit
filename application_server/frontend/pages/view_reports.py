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

def sync_reports_with_session():
    reports = list_reports()
    
    # Add any reports from the server that aren't in session state
    for job_id, info in reports.items():
        if job_id not in st.session_state.jobs:
            st.session_state.jobs[job_id] = info
    
    return reports

def on_report_select():
    # This will be called when the selectbox value changes
    selected_job = st.session_state.selectbox_reports
    if selected_job and selected_job != "Select a report to view":
        st.session_state.selected_job = selected_job
    else:
        st.session_state.selected_job = None

def main():
    st.header("View Audit Reports")
    
    # Get list of completed reports and sync with session state
    reports = sync_reports_with_session()
    
    if reports:
        # Create a data frame for easier display
        report_data = []
        for job_id, info in reports.items():
            report_data.append({
                "Job ID": job_id,
                "Case Number": info.get("case_number", "Unknown"),
                "Status": info.get("status", "Unknown"),
                "Timestamp": info.get("timestamp", "Unknown"),
                "Report URL": info.get("report_url", "")
            })
        
        df = pd.DataFrame(report_data)
        st.dataframe(df[["Case Number", "Status", "Timestamp"]])
        
        # Add the default "Select a report" option
        options = ["Select a report to view"] + [r["Job ID"] for r in report_data]
        
        # Format function for the dropdown
        def format_option(x):
            if x == "Select a report to view":
                return x
            return f"Case {[r['Case Number'] for r in report_data if r['Job ID'] == x][0]} ({[r['Timestamp'] for r in report_data if r['Job ID'] == x][0]})"
        
        col1, col2 = st.columns([3,7])

        with col1:
            # Allow selecting a report to view with auto-update on change
            selected_job = st.selectbox(
                "Select a report to view:", 
                options=options,
                format_func=format_option,
                key="selectbox_reports",
                on_change=on_report_select
            )   
        
        # Display the report if one is selected
        if st.session_state.selected_job:
            job_id = st.session_state.selected_job
            
            # For reused job IDs, we might need special handling
            if job_id.startswith("reused_") and job_id not in st.session_state.jobs:
                # Try to extract the case number
                parts = job_id.split("_")
                if len(parts) > 1:
                    case_number = parts[1]
                    st.info(f"Loading existing report for case {case_number}...")
                    
                    # Look for this case number in the reports list
                    reports = list_reports()
                    for report_id, info in reports.items():
                        if info.get("case_number") == case_number:
                            # Found a matching report - use its info
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
                
                # Add delete button at the end of the report
                if st.button("Delete This Report", type="secondary"):
                    if st.session_state.get("confirm_delete") == case_id:
                        # User has confirmed, proceed with deletion
                        success, message = delete_report(case_id)
                        if success:
                            st.success(message)
                            # Reset selection
                            st.session_state.selected_job = None
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
    else:
        st.info("No reports available. Upload a case PDF for analysis.")

if __name__ == "__main__":
    main() 