# Client-Server Architecture for TIBCO Case Audit

## Overview

The TIBCO Case Audit application can be restructured into a client-server architecture with:

1. **FastAPI Backend**: Handles PDF processing, AI analysis, and report generation
2. **Streamlit Frontend**: Provides a user-friendly interface for uploading PDFs and viewing reports

## Key Components

### Backend (FastAPI)

- **Endpoints**:
  - `/upload/`: Accept PDF files for processing
  - `/status/{job_id}`: Check processing status
  - `/report/{job_id}`: Retrieve generated audit reports
  - `/reports/`: List all available reports

- **Processing Logic**:
  - Background tasks for PDF extraction and analysis
  - Asynchronous processing for better performance
  - Stateful job tracking (could use a database in production)

- **Code Reuse**:
  - Existing pdf_extractor.py service
  - Existing ai_analyzer.py service
  - Existing report_generator.py service

### Frontend (Streamlit)

- **User Interface**:
  - PDF upload with drag and drop
  - Processing status indicators
  - Report viewing with markdown rendering
  - Historical report browsing

- **API Communication**:
  - HTTP requests to backend endpoints
  - Polling for status updates
  - Downloading and displaying reports

## Benefits

1. **Better User Experience**: Web-based interface accessible from any browser
2. **Multi-User Support**: Multiple users can use the system simultaneously
3. **Scalability**: Backend can be scaled independently of the frontend
4. **Separation of Concerns**: UI logic separate from processing logic

## Implementation Steps

1. Refactor existing code to work as API services
2. Build FastAPI backend with endpoints as described
3. Create Streamlit frontend for user interaction
4. Add proper error handling and status tracking
5. Implement secure authentication if needed
6. Deploy as separate services (could use containers)

## Technical Requirements

- FastAPI for the backend API
- Streamlit for the frontend interface
- Database for persistent storage (optional)
- Proper authentication system (optional)
- Cloud hosting or on-premises deployment

## Conclusion

The client-server architecture would enhance the TIBCO Case Audit tool by making it more user-friendly, scalable, and accessible. The existing core logic can be reused with minimal changes, while gaining all the benefits of a modern web application. 