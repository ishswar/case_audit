# TIBCO Case Audit - Client-Server Architecture

This folder contains a conceptual exploration of how the TIBCO Case Audit application could be restructured as a client-server application using:

- **Backend**: FastAPI for a robust API server
- **Frontend**: Streamlit for a user-friendly web interface

## Architecture Overview

![Architecture Diagram](https://mermaid.ink/img/pako:eNptkc1uwjAQhF9l5QOXQhMEJDnkgKBViyio1FblYhJDLGLHsrdS-ffdOApUxJfJ982s7cx2YSMNsJy12mzZ1dM5fZj119NuZ4zGplEWvMf6WBrwoP3OQX-m9-68Ut7ZPdz5g9uDf1BVrUzuanPlujfvYFqpUWaOvyh-KAR0s7kPGjrjRXgMGYzxYhEWsxDGEAwZckcxFCk1xxRxiZNJnISJaGMULFNb0_Sk6q0Fm3OhBNVb9oFtfdM8tQ1uBVbbxNcS94xXrYOzVYZ29GiSQu-Xje6FoGjhxnrxyjg_7qh8FYKGPTYGJcsJVV5QrtumAB0KSHl9RP1KXMHlnGBjyj4TyRitHf3Pf5iWUCobrGhD-4wZgx1OHRRalsvw55KUP_ADkQ9Oi-kz-NiuqJvlH8Nulco?)

### Components

1. **FastAPI Backend**
   - **PDF Upload Endpoint**: Accepts PDF files for processing
   - **Background Processing**: Handles PDF extraction, AI analysis, and report generation asynchronously 
   - **Status Tracking**: Provides job status updates
   - **Report Retrieval**: Serves generated audit reports

2. **Streamlit Frontend**
   - **User Interface**: Clean, interactive web interface
   - **File Upload**: Simple PDF upload with drag-and-drop
   - **Status Monitoring**: Real-time processing status updates
   - **Report Viewing**: Displays formatted audit reports
   - **Report Management**: Lists and allows access to historical reports

### Data Flow

1. User uploads a PDF through the Streamlit interface
2. Frontend sends the PDF to the backend API
3. Backend generates a job ID and begins processing in the background
4. Frontend periodically checks job status
5. When processing completes, the report is available for viewing
6. User can download reports in Markdown format

## Benefits of This Architecture

1. **Separation of Concerns**:
   - Frontend focuses on user experience
   - Backend handles processing logic and data management

2. **Scalability**:
   - Backend can be scaled independently of the frontend
   - Multiple users can access the system simultaneously
   - Processing can happen on more powerful servers

3. **Improved User Experience**:
   - Responsive web interface
   - Real-time status updates
   - Ability to view historical reports

4. **Deployment Flexibility**:
   - Backend can be deployed as a containerized service
   - Frontend can be hosted separately
   - Components can be distributed across multiple servers

## How to Implement This Architecture

### 1. Adapt Existing Code

The current application logic can be moved to the FastAPI backend:
- `pdf_extractor.py` for PDF processing
- `ai_analyzer.py` for AI analysis
- `report_generator.py` for report generation

### 2. Create API Endpoints

Implement REST API endpoints as shown in the conceptual code:
- `/upload/` for PDF upload
- `/status/{job_id}` for checking processing status
- `/report/{job_id}` for retrieving generated reports
- `/reports/` for listing available reports

### 3. Build Streamlit Frontend

Create a Streamlit app that communicates with the backend API:
- File upload interface
- Status monitoring
- Report viewing
- Report listing and management

### 4. Setup Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backend (from backend directory)
uvicorn main:app --reload

# Run the frontend (from frontend directory)
streamlit run app.py
```

## Deployment Considerations

- **Docker**: Containerize both frontend and backend
- **Environment Variables**: Use environment variables for configuration
- **Authentication**: Add authentication for secure access
- **Database**: Replace in-memory storage with a proper database
- **Cloud Deployment**: Deploy on cloud platforms like AWS, GCP, or Azure

## Next Steps

1. Implement the basic API endpoints
2. Build the Streamlit frontend
3. Test with sample PDFs
4. Add authentication and user management
5. Set up proper database storage
6. Containerize the application
7. Deploy to production environment 