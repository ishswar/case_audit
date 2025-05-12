import os
import textwrap
import re
from app.models.audit import AuditReport
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        
    def _wrap_text(self, text, max_width=80):
        """Wrap text to ensure it stays within bounds."""
        if not text:
            return ""
        return textwrap.fill(text, max_width)
    
    def _format_for_markdown_table(self, text, max_width=60):
        """Format text for displaying in a Markdown table cell.
        Uses spaces to create properly formatted markdown content without line breaks."""
        if not text:
            return ""
            
        # Use a smaller max width for table cells to prevent overflow
        lines = []
        for line in textwrap.wrap(text, max_width):
            lines.append(line)
            
        # Join lines with a space instead of <br> to avoid rendering issues
        return " ".join(lines)

    def generate_report(self, report: AuditReport):
        """Generate a Markdown report."""
        
        # Debug: Print case summary at the start
        print(f"\nDEBUG - Report Generator received case_summary: '{report.case_summary}'")
        print(f"DEBUG - case_summary type: {type(report.case_summary)}")
        print(f"DEBUG - case_summary is empty: {not bool(report.case_summary)}")
        
        # Create markdown content
        markdown = []
        
        # Title
        markdown.append("# Case Quality Audit Report\n")
        
        # Case Info
        markdown.append("## Case Information\n")
        markdown.append(f"**Case Number:** {report.case_info.case_number}  ")
        markdown.append(f"**Customer:** {report.case_info.customer_name}  ")
        markdown.append(f"**Product:** {report.case_info.product_name} {report.case_info.product_version}  ")
        markdown.append(f"**Severity:** {report.case_info.severity}  ")
        markdown.append(f"**Status:** {report.case_info.status}  ")
        markdown.append(f"**Created:** {report.case_info.date_created.strftime('%Y-%m-%d %H:%M:%S')}  ")
        markdown.append(f"**Closed:** {report.case_info.date_closed.strftime('%Y-%m-%d %H:%M:%S')}  ")
        markdown.append(f"**Subject:** {self._wrap_text(report.case_info.subject, 80)}\n")
        
        # Add Case Summary after Case Information if available
        if report.case_summary:
            print(f"DEBUG - Adding case summary to report: '{report.case_summary}'")
            markdown.append("\n## Case Summary\n")
            markdown.append("*Quick highlights of the case:*\n")
            markdown.append(self._wrap_text(report.case_summary))
            markdown.append("")
        else:
            print("DEBUG - No case summary to add to report!")
        
        # Ratings
        markdown.append("\n## Quality Ratings\n")
        markdown.append("| Category | Rating | Description |")
        markdown.append("| --- | :---: | --- |")
        markdown.append(f"| Initial Response | {report.ratings.initial_response}/5 | {self._format_for_markdown_table(report.initial_response_feedback)} |")
        markdown.append(f"| Problem Diagnosis | {report.ratings.problem_diagnosis}/5 | {self._format_for_markdown_table(report.problem_diagnosis_feedback)} |")
        markdown.append(f"| Technical Accuracy | {report.ratings.technical_accuracy}/5 | {self._format_for_markdown_table(report.technical_accuracy_feedback)} |")
        markdown.append(f"| Solution Quality | {report.ratings.solution_quality}/5 | {self._format_for_markdown_table(report.solution_feedback)} |")
        markdown.append(f"| Communication | {report.ratings.communication}/5 | {self._format_for_markdown_table(report.communication_feedback)} |")
        markdown.append(f"| Overall Experience | {report.ratings.overall_experience}/5 | {self._format_for_markdown_table(report.overall_feedback)} |\n")
        
        # Detailed Feedback
        markdown.append("\n## Detailed Feedback\n")
        
        # Initial Response section
        markdown.append("### Initial Response\n")
        markdown.append(self._wrap_text(report.initial_response_feedback))
        markdown.append("")
        
        # Problem Diagnosis section
        markdown.append("### Problem Diagnosis\n")
        markdown.append(self._wrap_text(report.problem_diagnosis_feedback))
        markdown.append("")
        
        # Technical Accuracy section
        markdown.append("### Technical Accuracy\n")
        markdown.append(self._wrap_text(report.technical_accuracy_feedback))
        markdown.append("")
        
        # Solution Quality section
        markdown.append("### Solution Quality\n")
        markdown.append(self._wrap_text(report.solution_feedback))
        markdown.append("")
        
        # Communication section
        markdown.append("### Communication\n")
        markdown.append(self._wrap_text(report.communication_feedback))
        markdown.append("")
        
        # Overall assessment
        markdown.append("### Overall Assessment\n")
        markdown.append(self._wrap_text(report.overall_feedback))
        markdown.append("")
        
        # Recommendations
        markdown.append("\n## Recommendations\n")
        
        # Process recommendations 
        # First clean up the recommendations string to remove any existing numbered format
        clean_recommendations = re.sub(r'\d+[\.\)\s]*', '', report.recommendations)
        
        # Split by period to get individual recommendations
        recommendations = [rec.strip() for rec in clean_recommendations.split('.') if rec.strip()]
        
        # Format as numbered list items
        for i, rec in enumerate(recommendations, 1):
            markdown.append(f"{i}. {rec}")
        
        # Add timestamp at the end of the report
        generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        markdown.append(f"\n\n*Report generated on: {generation_time}*")
        
        # Write to file
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w') as f:
            f.write('\n'.join(markdown))
            
        return self.output_path 