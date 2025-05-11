# TIBCO Case Quality Audit Tool

A tool for analyzing TIBCO support case PDFs and generating quality audit reports in Markdown format.

## Overview

This tool helps quality assurance teams evaluate support cases by:
1. Extracting information from TIBCO support case PDFs
2. Analyzing the case content using AI (Google Gemini)
3. Generating detailed quality audit reports in Markdown format

## Features

- Automatic PDF extraction of case details
- AI-powered analysis of support quality across multiple dimensions
- Customizable evaluation criteria
- Clean, organized Markdown reports
- One report per case ID (overwrites previous audits of the same case)

## Project Structure

```
case_audit/
├── app/
│   ├── models/         # Pydantic data models
│   ├── services/       # Core functionality
│   └── main.py         # Application entry point
└── audit_reports/      # Generated audit reports
```

## How to Use

1. Place your TIBCO case PDF in the `app/` directory
2. Run the tool:
   ```
   python -m app.main
   ```
3. View the generated report in the `audit_reports/` directory

## Requirements

- Python 3.8+
- PyPDF2
- Google Generative AI (Gemini)

## Sample Output

The tool generates comprehensive Markdown reports that include:
- Case information (Case number, Customer, Product, etc.)
- Quality ratings across multiple dimensions
- Detailed feedback in each area
- Specific recommendations for improvement

## Development

This project was created to streamline the case quality audit process. Future enhancements may include:
- Support for batch processing of multiple PDFs
- Additional evaluation metrics
- Dashboard for tracking quality trends
- Export to different formats (PDF, HTML, etc.)

## License

This project is available for use under the MIT License.
