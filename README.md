# TIBCO Case Quality Audit Tool

A tool for analyzing TIBCO support case PDFs and generating quality audit reports in Markdown format using Google's Gemini AI.

## Overview

This tool helps quality assurance teams evaluate support cases by:
1. Extracting information from TIBCO support case PDFs
2. Analyzing the case content using Google's Gemini AI
3. Generating detailed quality audit reports in Markdown format
4. Providing a web-based interface for uploading PDFs and viewing reports

## Features

- Client-server architecture with FastAPI backend and Streamlit frontend
- Automatic PDF extraction of case details
- AI-powered analysis of support quality across multiple dimensions
- Clean, organized Markdown reports
- Duplicate handling to prevent processing the same case multiple times
- Application state management and reset functionality
- Multi-page navigation in the frontend
- Docker support for containerized deployment

## Project Structure

```
case_audit/
├── application_server/     # Client-server implementation
│   ├── backend/            # FastAPI server
│   │   ├── jobs/           # Job tracking storage
│   │   ├── main.py         # API endpoints
│   │   ├── reset_app.py    # Reset utility
│   │   └── clean_duplicate_jobs.py  # Cleanup utility
│   └── frontend/           # Streamlit interface
│       ├── pages/          # Multi-page components
│       └── main.py         # Frontend entry point
├── app/                    # Core application services
│   ├── models/             # Pydantic data models
│   ├── services/           # Core functionality modules
│   │   ├── pdf_extractor.py   # PDF parsing
│   │   ├── ai_analyzer.py     # Google Gemini integration
│   │   └── report_generator.py # Markdown report creation
│   └── main.py             # Original CLI application
├── pdf_uploads/            # Storage for uploaded PDFs
├── audit_reports/          # Generated audit reports
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose configuration
├── docker-entrypoint.sh    # Container entry point script
└── requirements.txt        # Project dependencies
```

## Getting Started

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd case_audit

# Install dependencies
pip install -r requirements.txt

# Set up environment variables for Google Gemini API
export PROJECT_ID=your-google-project-id
export LOCATION=global
```

### Running the Application

#### Docker (Recommended)

The easiest way to run the application is using Docker Compose:

```bash
# Set your Google Gemini API credentials
export PROJECT_ID=your-google-project-id
export LOCATION=global

# Start the application with Docker Compose
docker-compose up -d

# Alternative: Run as a single container
docker-compose --profile combined up combined -d
```

Access the frontend at http://localhost:8501

#### Client-Server Mode (Local Development)

```bash
# Start the backend server
cd application_server/backend
uvicorn main:app --reload --port 8000

# In a separate terminal, start the frontend
cd application_server/frontend
streamlit run main.py
```

Then open your browser to http://localhost:8501 to access the web interface.

#### CLI Mode (Legacy)

```bash
# Run the CLI tool directly
python -m app.main /path/to/tibco_case.pdf
```

## Using the Web Interface

1. Navigate to the "Upload Cases" page
2. Upload a TIBCO case PDF file
3. Monitor processing status
4. Switch to the "View Reports" page to see audit results

## Administration

- Reset application state: `curl -X POST "http://localhost:8000/admin/reset?clear_jobs=true"`
- Clean up duplicate entries: Run `python application_server/backend/clean_duplicate_jobs.py`

### Docker Administration

- View logs: `docker-compose logs -f`
- Restart services: `docker-compose restart`
- Stop the application: `docker-compose down`
- Rebuild containers: `docker-compose build`

## Sample Output

The tool generates comprehensive Markdown reports that include:
- Case information (Case number, Customer, Product, etc.)
- Quality ratings across multiple dimensions
- Detailed feedback in each area
- Specific recommendations for improvement

## Development

### Recent Updates

- Added Docker support for containerized deployment
- Implemented client-server architecture with FastAPI and Streamlit
- Added multi-page navigation in the frontend
- Fixed duplicate case handling to prevent redundant processing
- Added application reset and cleanup utilities
- Improved error handling and logging

### Future Enhancements

- Dashboard for tracking quality trends
- Export to different formats (PDF, HTML)
- User authentication and role-based access
- Integration with ticketing systems

## License

This project is available for use under the MIT License.
