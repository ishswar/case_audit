# TIBCO Case Audit - Client-Server Architecture

This application processes TIBCO Support Case PDFs using Google's Gemini AI and generates quality audit reports. It follows a client-server architecture with a FastAPI backend and Streamlit frontend.

## Architecture Overview

![Architecture Diagram](https://mermaid.ink/img/pako:eNptkc1uwjAQhF9l5QOXQhMEJDnkgKBViyio1FblYhJDLGLHsrdS-ffdOApUxJfJ982s7cx2YSMNsJy12mzZ1dM5fZj119NuZ4zGplEWvMf6WBrwoP3OQX-m9-68Ut7ZPdz5g9uDf1BVrUzuanPlujfvYFqpUWaOvyh-KAR0s7kPGjrjRXgMGYzxYhEWsxDGEAwZckcxFCk1xxRxiZNJnISJaGMULFNb0_Sk6q0Fm3OhBNVb9oFtfdM8tQ1uBVbbxNcS94xXrYOzVYZ29GiSQu-Xje6FoGjhxnrxyjg_7qh8FYKGPTYGJcsJVV5QrtumAB0KSHl9RP1KXMHlnGBjyj4TyRitHf3Pf5iWUCobrGhD-4wZgx1OHRRalsvw55KUP_ADkQ9Oi-kz-NiuqJvlH8Nulco?)

## Recent Updates

### Navigation Improvements
- Implemented Streamlit's navigation feature to replace tabs for better page organization
- Split the application into separate pages for uploading cases and viewing reports
- Added a logo to the application for branding

### Duplicate Entry Handling
- Fixed an issue where uploading the same PDF multiple times created duplicate entries in all_jobs.json
- Implemented a simplified approach that keeps only one job entry per case number
- Added proper tracking of processed case numbers to prevent duplicates

### Application Reset Functionality
- Added an API endpoint to reset the application state
- Created standalone scripts to clean up the jobs file:
  - `reset_app.py`: Reset processed case numbers and job entries
  - `clean_duplicate_jobs.py`: Remove duplicate entries for the same case number

### Backend Improvements
- Fixed type mismatches in debugging configuration
- Improved error handling for PDF processing
- Added better logging for case detection
- Upgraded Streamlit to version 1.45.0

## Components

### FastAPI Backend
- **PDF Upload Endpoint**: Accepts PDF files and handles duplicate detection
- **Background Processing**: Processes PDFs with Google Gemini AI
- **Status Tracking**: Provides job status updates
- **Report Retrieval**: Serves generated audit reports
- **Admin Endpoints**: Reset and maintenance functionality

### Streamlit Frontend
- **Upload Page**: Interface for PDF uploads with status updates
- **Reports Page**: Browse and view generated audit reports
- **Status Indicators**: Real-time processing status updates

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backend (from application_server/backend directory)
uvicorn main:app --reload --port 8000

# Run the frontend (from application_server/frontend directory)
streamlit run main.py
```

### Usage

1. Navigate to the Upload Cases page
2. Upload a TIBCO case PDF file
3. Monitor processing status
4. Navigate to the View Reports page to see audit results

### Admin Tools

- API Reset: `curl -X POST "http://localhost:8000/admin/reset?clear_jobs=true"`
- Clean duplicate entries: `python backend/clean_duplicate_jobs.py`

## Deployment Considerations

- **Environment Variables**: Store API keys and configuration securely
- **Database**: Consider using a proper database instead of file storage for production
- **Authentication**: Add user authentication for secure access
- **Container Deployment**: Consider Docker for containerized deployment 