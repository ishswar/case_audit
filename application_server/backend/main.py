from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from typing import List, Optional
import uvicorn
from pydantic import BaseModel
import tempfile
import sys
import glob
import re
import datetime
import json

# Add the parent directory to the Python path to allow importing from the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import our existing services
from app.services.pdf_extractor import PDFExtractor
from app.services.ai_analyzer import AIAnalyzer
from app.services.report_generator import ReportGenerator
from dotenv import load_dotenv

# Load environment variables for Google AI
load_dotenv()

app = FastAPI(title="TIBCO Case Audit API", 
              description="API for analyzing TIBCO support case quality")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Storage paths - using only the main project directories
UPLOAD_DIR = os.path.join(ROOT_DIR, "pdf_uploads")
REPORT_DIR = os.path.join(ROOT_DIR, "audit_reports")
JOBS_DIR = os.path.join(ROOT_DIR, "application_server", "backend", "jobs")
JOBS_FILE = os.path.join(JOBS_DIR, "all_jobs.json")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

# Get Google API configuration from environment variables
PROJECT_ID = os.getenv('PROJECT_ID', 'webfocus-devops')
LOCATION = os.getenv('LOCATION', 'global')

# Response models
class ProcessResponse(BaseModel):
    job_id: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    case_number: Optional[str] = None
    report_url: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None

class DeleteResponse(BaseModel):
    case_number: str
    message: str
    success: bool

# In-memory job tracking (would use a database in production)
jobs = {}

# Keep track of case numbers we've seen to avoid duplicates
processed_case_numbers = set()

# Function to get a formatted timestamp for a file
def get_file_timestamp(file_path):
    if not os.path.exists(file_path):
        return None
    
    # Get the modification time of the file
    mod_time = os.path.getmtime(file_path)
    dt = datetime.datetime.fromtimestamp(mod_time)
    
    # Format the date (e.g., "May 10, 2025 11:30 PM")
    return dt.strftime("%b %d, %Y %I:%M %p")

# Helper function to convert path to relative path for storage
def get_relative_path(full_path):
    if os.path.isabs(full_path):
        try:
            rel_path = os.path.relpath(full_path, ROOT_DIR)
            return rel_path
        except ValueError:
            # If paths are on different drives (Windows), just return the basename
            return os.path.basename(full_path)
    return full_path  # Already relative

# Helper function to get absolute path from a possibly relative path
def get_absolute_path(path):
    if os.path.isabs(path):
        return path
    return os.path.join(ROOT_DIR, path)

# Save all jobs to a single JSON file
def save_all_jobs():
    try:
        # Make a deep copy of jobs with relative paths for storage
        jobs_for_storage = {}
        for job_id, job_info in jobs.items():
            job_copy = dict(job_info)
            # Convert absolute paths to relative for storage
            if "report_url" in job_copy and job_copy["report_url"]:
                job_copy["report_url"] = get_relative_path(job_copy["report_url"])
            if "file_path" in job_copy and job_copy["file_path"]:
                job_copy["file_path"] = get_relative_path(job_copy["file_path"])
            jobs_for_storage[job_id] = job_copy
            
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs_for_storage, f, indent=2)
    except Exception as e:
        print(f"Error saving jobs: {e}")

# Save a single job (updates the full jobs file)
def save_job(job_id, job_info):
    job_info_copy = dict(job_info)  # Create a copy to avoid modifying the original
    job_info_copy["job_id"] = job_id  # Ensure job_id is included
    
    # Update the job in memory
    jobs[job_id] = job_info_copy
    
    # Save all jobs to file
    save_all_jobs()

# Load all jobs from the single file
def load_all_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    
    try:
        with open(JOBS_FILE, 'r') as f:
            loaded_jobs = json.load(f)
            
            # Convert any relative paths to absolute paths for use in the application
            for job_id, job_info in loaded_jobs.items():
                if "report_url" in job_info and job_info["report_url"]:
                    job_info["report_url"] = get_absolute_path(job_info["report_url"])
                if "file_path" in job_info and job_info["file_path"]:
                    job_info["file_path"] = get_absolute_path(job_info["file_path"])
                
                # Extract case numbers from all jobs to populate processed_case_numbers
                if "case_number" in job_info:
                    processed_case_numbers.add(job_info["case_number"])
                    
            return loaded_jobs
    except Exception as e:
        print(f"Error loading jobs: {e}")
        return {}

# Clean up the all_jobs.json file by removing duplicate entries for the same case
def clean_jobs_file():
    global jobs
    case_to_job_map = {}
    jobs_to_remove = []
    
    # First pass: find duplicate entries for each case number
    for job_id, job_info in jobs.items():
        if "case_number" in job_info:
            case_number = job_info["case_number"]
            
            # Keep the first entry we find for each case number
            if case_number not in case_to_job_map:
                case_to_job_map[case_number] = job_id
            else:
                # This is a duplicate entry for this case
                jobs_to_remove.append(job_id)
    
    # Second pass: remove duplicates
    for job_id in jobs_to_remove:
        if job_id in jobs:
            print(f"Removing duplicate entry: {job_id}")
            del jobs[job_id]
    
    # Save the cleaned jobs file
    if jobs_to_remove:
        print(f"Removed {len(jobs_to_remove)} duplicate entries")
        save_all_jobs()
        return len(jobs_to_remove)
    return 0

# Load existing reports at startup
def load_existing_reports():
    # Load all saved jobs first
    global jobs
    jobs = load_all_jobs()
    
    # Find all Markdown files in the main audit_reports directory
    report_files = glob.glob(os.path.join(REPORT_DIR, "*.md"))
    jobs_updated = False
    
    for report_file in report_files:
        filename = os.path.basename(report_file)
        # Extract case number from filename (case_XXXXXXX_audit.md)
        match = re.search(r'case_(\d+)_audit\.md', filename)
        if match:
            case_number = match.group(1)
            
            # Add to our tracked case numbers
            processed_case_numbers.add(case_number)
            
            # Check if we already have a job for this case number
            existing_job = None
            for job_id, job in jobs.items():
                if job.get("case_number") == case_number:
                    existing_job = job_id
                    break
            
            # Create a virtual job for this report if it doesn't exist
            if not existing_job:
                job_id = f"existing_{case_number}"
                
                # Get the file timestamp
                timestamp = get_file_timestamp(report_file)
                
                # Get relative path for storage
                rel_path = get_relative_path(report_file)
                
                # Create job info - use relative path in the structure
                job_info = {
                    "job_id": job_id,
                    "status": "completed",
                    "case_number": case_number,
                    "report_url": rel_path,  # Use relative path for storage consistency
                    "existing": True,
                    "timestamp": timestamp
                }
                
                # Save to memory - will be converted to absolute when needed
                jobs[job_id] = job_info
                jobs_updated = True
    
    # Clean up duplicate reused entries
    clean_jobs_file()
    
    # Save all jobs if we added any new ones
    if jobs_updated:
        save_all_jobs()

# Load existing reports on startup
load_existing_reports()

@app.post("/upload/", response_model=ProcessResponse)
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a TIBCO case PDF for processing"""
    try:
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Check if this PDF might be a duplicate by extracting case number first
        try:
            print(f"Checking file: {file.filename}")
            pdf_extractor = PDFExtractor(file_path)
            case_info = pdf_extractor.extract_case_info()
            case_number = case_info.case_number
            
            print(f"Extracted case number: {case_number}")
            print(f"Current processed case numbers: {processed_case_numbers}")
            
            # Check if we've seen this case number before and if a report exists
            existing_report_path = os.path.join(REPORT_DIR, f"case_{case_number}_audit.md")
            
            # Look for existing job entry for this case number
            existing_job_id = None
            for existing_id, existing_info in jobs.items():
                if existing_info.get("case_number") == case_number:
                    existing_job_id = existing_id
                    break
            
            if existing_job_id and os.path.exists(existing_report_path):
                print(f"Case {case_number} already processed with job ID {existing_job_id}")
                
                # Use the existing job ID - no need to create a new entry
                # Clean up the temporary uploaded file since we don't need it
                try:
                    os.remove(file_path)
                    print(f"Removed temporary file: {file_path}")
                except Exception as e:
                    print(f"Error removing file: {e}")
                
                # Add to processed case numbers if not already there
                processed_case_numbers.add(case_number)
                
                return {"job_id": existing_job_id, "message": f"Using existing report for case {case_number}"}
            
            # If the report exists but no job entry (perhaps from a manual reset), create a single entry
            if os.path.exists(existing_report_path) and not existing_job_id:
                print(f"Found existing report for case {case_number} but no job entry")
                
                # Add to processed_case_numbers
                processed_case_numbers.add(case_number)
                
                # Create a simple job entry with the original UUID
                timestamp = get_file_timestamp(existing_report_path)
                
                # Get relative path for storage consistency
                rel_path = get_relative_path(existing_report_path)
                
                job_info = {
                    "job_id": job_id,
                    "status": "completed",
                    "case_number": case_number,
                    "report_url": rel_path,
                    "timestamp": timestamp
                }
                
                # Save to memory and disk
                save_job(job_id, job_info)
                
                # Clean up the temporary uploaded file since we don't need it
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file: {e}")
                    
                return {"job_id": job_id, "message": f"Found existing report for case {case_number}"}
                
        except Exception as e:
            print(f"Error checking for duplicate: {e}")
            # Continue with normal processing if we can't check for duplicates
            
        # Get relative file path for storage
        rel_file_path = get_relative_path(file_path)
        
        # Start background processing for new file
        job_info = {
            "job_id": job_id, 
            "status": "pending", 
            "file_path": rel_file_path,
            "timestamp": datetime.datetime.now().strftime("%b %d, %Y %I:%M %p")
        }
        
        # Save to memory and disk
        save_job(job_id, job_info)
        
        # Start processing
        background_tasks.add_task(process_pdf, job_id, file_path)
        
        return {"job_id": job_id, "message": "PDF uploaded and processing started"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Check the status of a processing job"""
    # Try to reload all jobs if this job isn't found
    global jobs
    if job_id not in jobs:
        jobs = load_all_jobs()
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Make sure job_id is included in the data
    job_data = dict(jobs[job_id])
    if "job_id" not in job_data:
        job_data["job_id"] = job_id
    
    return JobStatus(**job_data)

@app.get("/report/{job_id}")
async def get_report(job_id: str):
    """Get the generated audit report for a completed job"""
    # Try to reload all jobs if this job isn't found
    global jobs
    if job_id not in jobs:
        jobs = load_all_jobs()
        
        # Special handling for reused_/existing_ jobs
        if job_id not in jobs and (job_id.startswith("reused_") or job_id.startswith("existing_")):
            parts = job_id.split("_")
            if len(parts) > 1:
                case_number = parts[1]
                report_path = os.path.join(REPORT_DIR, f"case_{case_number}_audit.md")
                if os.path.exists(report_path):
                    # Get relative path for storage consistency
                    rel_path = get_relative_path(report_path)
                    
                    # Recreate the job entry
                    timestamp = get_file_timestamp(report_path)
                    job_info = {
                        "job_id": job_id,
                        "status": "completed",
                        "case_number": case_number,
                        "report_url": rel_path,  # Store relative path
                        "timestamp": timestamp,
                        "note": f"Recreated job for case {case_number}"
                    }
                    save_job(job_id, job_info)
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not yet available")
    
    # Get the report path, ensuring it's an absolute path
    report_path = job["report_url"]
    if not os.path.isabs(report_path):
        report_path = os.path.join(ROOT_DIR, report_path)
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(report_path, media_type="text/markdown")

@app.get("/reports/")
async def list_reports():
    """List all completed reports"""
    # Refresh jobs from disk to ensure we have the latest
    global jobs
    jobs = load_all_jobs()
    
    # Get completed jobs
    completed_jobs = {
        job_id: job for job_id, job in jobs.items() 
        if job["status"] == "completed"
    }
    
    return completed_jobs

@app.delete("/report/{case_number}", response_model=DeleteResponse)
async def delete_report(case_number: str):
    """Delete an audit report and its job entries"""
    global jobs
    # Make sure we have the latest job data
    jobs = load_all_jobs()
    
    # Find the report file
    report_path = os.path.join(REPORT_DIR, f"case_{case_number}_audit.md")
    if not os.path.exists(report_path):
        return DeleteResponse(
            case_number=case_number,
            message=f"Report file for case {case_number} not found",
            success=False
        )
    
    # Find all job entries related to this case number
    jobs_to_delete = []
    for job_id, job in jobs.items():
        if job.get("case_number") == case_number:
            jobs_to_delete.append(job_id)
    
    if not jobs_to_delete:
        return DeleteResponse(
            case_number=case_number,
            message=f"No job entries found for case {case_number}",
            success=False
        )
    
    # Delete the report file
    try:
        os.remove(report_path)
    except Exception as e:
        return DeleteResponse(
            case_number=case_number,
            message=f"Error deleting report file: {str(e)}",
            success=False
        )
    
    # Remove job entries
    for job_id in jobs_to_delete:
        jobs.pop(job_id, None)
    
    # Remove from processed case numbers
    processed_case_numbers.discard(case_number)
    
    # Save updated jobs data
    save_all_jobs()
    
    return DeleteResponse(
        case_number=case_number,
        message=f"Successfully deleted report for case {case_number} and {len(jobs_to_delete)} related job entries",
        success=True
    )

async def process_pdf(job_id: str, file_path: str):
    """Background task to process a PDF"""
    try:
        # Update job status to processing
        jobs[job_id]["status"] = "processing"
        save_job(job_id, jobs[job_id])
        
        # Use our existing processing code
        # Extract PDF content
        pdf_extractor = PDFExtractor(file_path)
        case_info = pdf_extractor.extract_case_info()
        case_content = pdf_extractor.extract_text()
        
        # Check if we've already processed this case number (this should rarely happen due to upload checks)
        case_number = case_info.case_number
        existing_report_path = os.path.join(REPORT_DIR, f"case_{case_number}_audit.md")
        
        # Look for a different job with the same case number
        other_job_id = None
        for existing_id, existing_info in jobs.items():
            if existing_id != job_id and existing_info.get("case_number") == case_number:
                other_job_id = existing_id
                break
        
        # If another job already processed this case and the report exists, use it
        if other_job_id and os.path.exists(existing_report_path):
            timestamp = get_file_timestamp(existing_report_path)
            
            # Get relative path for storage consistency
            rel_path = get_relative_path(existing_report_path)
            
            # Update our job to point to the existing report
            jobs[job_id].update({
                "status": "completed",
                "case_number": case_number,
                "report_url": rel_path,
                "timestamp": timestamp
            })
            save_job(job_id, jobs[job_id])
            return
        
        # Add to our processed case numbers
        processed_case_numbers.add(case_number)
        
        # Analyze with AI
        analyzer = AIAnalyzer(project_id=PROJECT_ID, location=LOCATION)
        audit_report = analyzer.analyze_case(case_content, case_info)
        
        # Generate report
        report_path = os.path.join(REPORT_DIR, f"case_{case_number}_audit.md")
        report_generator = ReportGenerator(report_path)
        report_generator.generate_report(audit_report)
        
        # Get the timestamp of the newly created report
        timestamp = get_file_timestamp(report_path)
        
        # Get relative path for storage consistency
        rel_path = get_relative_path(report_path)
        
        # Update job status
        jobs[job_id].update({
            "job_id": job_id,
            "status": "completed",
            "case_number": case_number,
            "report_url": rel_path,  # Store relative path
            "timestamp": timestamp
        })
        save_job(job_id, jobs[job_id])
        
    except Exception as e:
        # Update job status to failed
        jobs[job_id].update({
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        })
        save_job(job_id, jobs[job_id])

@app.post("/admin/clean-jobs-file")
async def clean_jobs_file_endpoint():
    """Admin endpoint to manually clean up duplicate reused entries in the all_jobs.json file"""
    try:
        before_count = len(jobs)
        clean_jobs_file()
        after_count = len(jobs)
        removed = before_count - after_count
        
        return {
            "success": True,
            "message": f"Cleaned up job file. Removed {removed} duplicate entries.",
            "before_count": before_count,
            "after_count": after_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning jobs file: {str(e)}")

@app.post("/admin/reset", response_model=dict)
async def reset_app(clear_jobs: bool = False):
    """Admin API to reset the application state"""
    global processed_case_numbers, jobs
    
    # Clear the set of processed case numbers
    count = len(processed_case_numbers)
    processed_case_numbers.clear()
    
    # Optionally clear all jobs
    jobs_count = 0
    if clear_jobs:
        jobs_count = len(jobs)
        jobs.clear()
        save_all_jobs()
    
    return {
        "message": f"Reset complete. Cleared {count} case numbers and {jobs_count} jobs.",
        "cleared_cases": count,
        "cleared_jobs": jobs_count
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 