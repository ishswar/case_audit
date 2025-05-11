import PyPDF2
from datetime import datetime
import re
from ..models.audit import CaseInfo

class PDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_text(self) -> str:
        """Extract all text from the PDF file."""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {e}")

    def _safe_extract_value(self, line: str) -> str:
        """Safely extract value after the colon, handling multiple colons."""
        parts = line.split(':')
        if len(parts) > 1:
            return ':'.join(parts[1:]).strip()
        return ""

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from various formats found in PDF."""
        if not date_str:
            return datetime.now()
        
        # Try to find and extract date patterns in the text
        # Pattern: MM-DD-YYYY HH:MM:SS
        date_match = re.search(r'(\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{1,2}:\d{1,2})', date_str)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%m-%d-%Y %H:%M:%S')
            except ValueError:
                pass
        
        # Pattern: MM-DD-YYYY
        date_match = re.search(r'(\d{1,2}-\d{1,2}-\d{4})', date_str)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%m-%d-%Y')
            except ValueError:
                pass
        
        # Additional common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        # Last resort: check if date is in the raw text format from PDF
        # Look for date patterns in the text (e.g., "12-03-2024 01:36:36")
        full_date_match = re.search(r'(\d{1,2}-\d{1,2}-\d{4})\s+(\d{1,2}:\d{1,2}:\d{1,2})', date_str)
        if full_date_match:
            date_part = full_date_match.group(1)
            time_part = full_date_match.group(2)
            try:
                return datetime.strptime(f"{date_part} {time_part}", '%m-%d-%Y %H:%M:%S')
            except ValueError:
                pass
        
        print(f"Warning: Could not parse date '{date_str}', using current time")
        return datetime.now()

    def extract_case_info(self) -> CaseInfo:
        """Extract and structure case information from the PDF."""
        text = self.extract_text()
        try:
            lines = text.split('\n')
            case_info = {
                'case_number': '',
                'product_version': '',
                'product_name': '',
                'customer_name': '',
                'severity': '',
                'status': '',
                'subject': '',
                'case_owner': '',
                'date_created': datetime.now(),
                'date_closed': datetime.now()
            }
            
            # Extract case number from the text first (often appears in multiple places)
            case_number_match = re.search(r'Case Number:?\s*(\d+)', text, re.IGNORECASE)
            if case_number_match:
                case_info['case_number'] = case_number_match.group(1).strip()
            
            # Extract creation date from the text
            date_created_match = re.search(r'Date/Time Created\s+(\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{1,2}:\d{1,2})', text, re.IGNORECASE)
            if date_created_match:
                case_info['date_created'] = self._parse_date(date_created_match.group(1))
            
            # Extract closed date from the text
            date_closed_match = re.search(r'Date/Time Closed\s+(\d{1,2}-\d{1,2}-\d{4}\s+\d{1,2}:\d{1,2}:\d{1,2})', text, re.IGNORECASE)
            if date_closed_match:
                case_info['date_closed'] = self._parse_date(date_closed_match.group(1))
            
            # Improved product name extraction
            # Look for specific fields that are more likely to contain just the product info
            product_name_match = re.search(r'Product Name\s+([^\n]+)', text)
            if product_name_match:
                case_info['product_name'] = product_name_match.group(1).strip()
            else:
                # Fallback extraction
                product_match = re.search(r'Product:?\s*([^:]+)', text, re.IGNORECASE)
                if product_match:
                    full_product = product_match.group(1).strip()
                    # Try to get just the first part before any email or other fields
                    product_parts = re.split(r'\s+(?=Contact|Email|Customer)', full_product)
                    if product_parts:
                        case_info['product_name'] = product_parts[0].strip()
                        # Check if the first part contains a version
                        version_match = re.search(r'Version\s+([0-9.]+)', product_parts[0])
                        if version_match:
                            case_info['product_version'] = version_match.group(1).strip()
                
            # If product name is still too long or seems to contain other fields, truncate it
            if len(case_info['product_name']) > 50:
                # Try to extract TIBCO product name specifically
                tibco_match = re.search(r'TIBCO\s+[\w\s]+(?:Edition|Container|Enterprise)', case_info['product_name'])
                if tibco_match:
                    case_info['product_name'] = tibco_match.group(0).strip()
                else:
                    # Just keep the first part
                    case_info['product_name'] = "TIBCO BusinessWorks"
                
            # Version extraction if still missing
            if not case_info['product_version']:
                version_match = re.search(r'Version\s+([0-9.]+)', text)
                if version_match:
                    case_info['product_version'] = version_match.group(1).strip()
            
            # Improved subject extraction
            # Try to find subject text more specifically
            subject_match = re.search(r'Subject\s+(Application[^\n]+)', text)
            if subject_match:
                case_info['subject'] = subject_match.group(1).strip()
            else:
                # Broader pattern
                subject_match = re.search(r'Subject:?\s*(.+?)(?=(?:\n\w+:|$))', text, re.IGNORECASE | re.DOTALL)
                if subject_match:
                    subject = subject_match.group(1).strip()
                    # Clean up multi-line subjects and limit length
                    subject = re.sub(r'\s+', ' ', subject)
                    
                    # If subject is too long, extract just the first sentence or clause
                    if len(subject) > 100:
                        first_part = re.split(r'(?<=[.!?])\s+', subject)[0]
                        if first_part and len(first_part) > 20:  # Ensure we have something meaningful
                            subject = first_part
                        else:
                            subject = subject[:100] + "..."
                    
                    case_info['subject'] = subject
            
            # Process each line for additional information
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if 'Customer' in line and not case_info['customer_name']:
                    customer_value = self._safe_extract_value(line)
                    if customer_value and len(customer_value) > 1:
                        case_info['customer_name'] = customer_value
                
                elif 'Severity' in line and not case_info['severity']:
                    severity_value = self._safe_extract_value(line)
                    if severity_value and len(severity_value) > 0:
                        case_info['severity'] = severity_value
                
                elif 'Status' in line and not case_info['status']:
                    status_value = self._safe_extract_value(line)
                    if status_value and len(status_value) > 0:
                        case_info['status'] = status_value
                
                elif 'Case Owner' in line and not case_info['case_owner']:
                    owner_value = self._safe_extract_value(line)
                    if owner_value and len(owner_value) > 1:
                        case_info['case_owner'] = owner_value

            return CaseInfo(**case_info)
        except Exception as e:
            raise Exception(f"Error parsing case information: {e}") 