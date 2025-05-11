import os
from datetime import datetime
from .services.pdf_extractor import PDFExtractor
from .services.ai_analyzer import AIAnalyzer
from .services.report_generator import ReportGenerator

def main():
    print("Extracting information from PDF...")
    
    # Input and output paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_pdf = os.path.join(current_dir, "TIBCO StandardReport_2468513.pdf")
    output_dir = "audit_reports"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Extract case information from PDF
        pdf_extractor = PDFExtractor(input_pdf)
        case_info = pdf_extractor.extract_case_info()
        case_content = pdf_extractor.extract_text()
        
        # Use the case number in the output filename
        case_number = case_info.case_number
        output_md = f"{output_dir}/case_{case_number}_audit.md"
        
        # Analyze the case with AI
        print("Analyzing case with AI...")
        analyzer = AIAnalyzer()
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
        
    except Exception as e:
        print(f"Error processing case: {e}")

if __name__ == "__main__":
    main() 