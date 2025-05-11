import os
import sys
import glob
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from .services.pdf_extractor import PDFExtractor
from .services.ai_analyzer import AIAnalyzer
from .services.report_generator import ReportGenerator

def process_pdf(pdf_path, output_dir, project_id, location):
    """Process a single PDF file and generate an audit report."""
    try:
        filename = os.path.basename(pdf_path)
        print(f"Extracting information from PDF: {filename}...")
        
        # Extract case information from PDF
        pdf_extractor = PDFExtractor(pdf_path)
        case_info = pdf_extractor.extract_case_info()
        case_content = pdf_extractor.extract_text()
        
        # Use the case number in the output filename
        case_number = case_info.case_number
        output_md = os.path.join(output_dir, f"case_{case_number}_audit.md")
        
        # Analyze the case with AI
        print("Analyzing case with AI...")
        analyzer = AIAnalyzer(project_id=project_id, location=location)
        
        try:
            audit_report = analyzer.analyze_case(case_content, case_info)
            
            # Generate the Markdown report
            print("Generating Markdown report...")
            report_generator = ReportGenerator(output_md)
            report_generator.generate_report(audit_report)
            
            print(f"Audit report generated successfully: {output_md}\n")
            
            # Display a summary in the terminal
            print("=== Case Quality Audit Report ===\n")
            print(f"Case Number: {audit_report.case_info.case_number}")
            print(f"Customer: {audit_report.case_info.customer_name}")
            print(f"Product: {audit_report.case_info.product_name} {audit_report.case_info.product_version}\n")
            
            print("Ratings:")
            print(f"Initial Response: {audit_report.ratings.initial_response}/5")
            print(f"Problem Diagnosis: {audit_report.ratings.problem_diagnosis}/5")
            print(f"Technical Accuracy: {audit_report.ratings.technical_accuracy}/5")
            print(f"Solution Quality: {audit_report.ratings.solution_quality}/5")
            print(f"Communication: {audit_report.ratings.communication}/5")
            print(f"Overall Experience: {audit_report.ratings.overall_experience}/5\n")
            
            print("Recommendations:")
            # Format recommendations as individual lines
            recommendations = audit_report.recommendations.split(".")
            for rec in recommendations:
                rec = rec.strip()
                if rec and not rec.isdigit():
                    # Clean up numbered format if present
                    if rec[0].isdigit() and len(rec) > 1 and rec[1] in ['.', ' ', ')']:
                        rec = rec[2:].strip() if rec[1] in ['.', ')'] else rec[1:].strip()
                    print(f"- {rec}")
            
            # Inform user about viewing the Markdown report
            print(f"\nFor a detailed report with all feedback, see {output_md}")
            print("You can view this Markdown file in any Markdown viewer or editor.")
            print("="*60 + "\n")
            
            return True
        except Exception as e:
            print(f"ERROR: AI analysis failed: {str(e)}")
            print("No audit report will be generated for this case.")
            print("="*60 + "\n")
            return False
        
    except Exception as e:
        print(f"Error processing case from PDF {os.path.basename(pdf_path)}: {e}")
        return False

def main():
    # Load environment variables
    # Look for .env file in the project root directory (one level up from app/)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, '.env')
    load_dotenv(env_path)
    
    # Get input directory from environment
    pdf_input_dir = os.getenv('PDF_INPUT_DIR')
    
    if not pdf_input_dir:
        print("Error: PDF_INPUT_DIR must be set in .env file")
        print("Please create a .env file based on .env.example")
        sys.exit(1)
    
    # Check if directory exists
    if not os.path.isdir(pdf_input_dir):
        print(f"Error: PDF input directory not found: {pdf_input_dir}")
        print("Please ensure the directory exists")
        sys.exit(1)
    
    # Find all PDF files in the input directory
    pdf_files = glob.glob(os.path.join(pdf_input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_input_dir}")
        print("Please add TIBCO case PDFs to the directory")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s) in {pdf_input_dir}")
    
    # Output directory for audit reports
    output_dir = os.path.join(root_dir, "audit_reports")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get Google API configuration from environment variables
    project_id = os.getenv('PROJECT_ID', 'webfocus-devops')
    location = os.getenv('LOCATION', 'global')
    
    # Process each PDF file
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        print(f"Processing {os.path.basename(pdf_file)}...")
        if process_pdf(pdf_file, output_dir, project_id, location):
            successful += 1
        else:
            failed += 1
    
    # Print summary
    print(f"Processing complete! Processed {len(pdf_files)} file(s)")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    # Exit with error code if any processing failed
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()