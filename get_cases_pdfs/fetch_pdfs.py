#!/usr/bin/env python3
"""
TIBCO Support Case Manager
Handles searching for cases and downloading PDFs from TIBCO support portal

Usage:
  - List cases only:               python fetch_pdfs.py list
  - Download first N cases:        python fetch_pdfs.py download --limit 5
  - Download all cases:            python fetch_pdfs.py download --all
  - Search for specific cases:     python fetch_pdfs.py list --query "BusinessWorks"
  - Filter by product:             python fetch_pdfs.py list --product "BusinessWorks"
  - List available products:       python fetch_pdfs.py products
  - Check authentication setup:    python fetch_pdfs.py setup

Authentication:
  This script requires authentication cookies from the TIBCO support portal.
  You can use the create_env.py utility to extract these from a curl command:
    python create_env.py command.txt
"""

import os
import sys
import json
import logging
import time
import subprocess
import requests
import argparse
import textwrap
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Tuple
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler("tibco_case_manager.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))


class TibcoCaseManager:
    """Manages TIBCO support case operations"""
    
    def __init__(self):
        """Initialize the case manager"""
        self.search_url = "https://api-support.tibco.com/es/ext/search_all_kbs"
        self.pdf_url_template = "https://api-support.tibco.com/request/pdf?requestId={request_id}&format=pdf&domain=support.tibco.com"
        
        # Get cookies from environment
        self.cookies = {
            "_biz_uid": os.getenv("BIZ_UID", "05daec6724484068bfd8e1e84a97448f"),
            "*biz*flagsA": os.getenv("BIZ_FLAGS", "%7B%22Version%22%3A1%2C%22ViewThrough%22%3A%221%22%2C%22XDomain%22%3A%221%22%7D"),
            "*biz*nA": os.getenv("BIZ_NA", "4"),
            "*biz*pendingA": os.getenv("BIZ_PENDING", "%5B%5D"),
            "opentoken": os.getenv("OPENTOKEN"),
            "opentoken-legacy": os.getenv("OPENTOKEN_LEGACY"),
            "csg-csm-d-zz-a-support": os.getenv("CSG_TOKEN")
        }
        
        # Common headers - using a more generic User-Agent
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
            "referer": "https://support.tibco.com/",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Unknown"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-site",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
        
        # Check if curl is available
        self.curl_available = self._check_curl_available()
        if not self.curl_available:
            logger.warning("Curl command not found. Will use Python requests instead")
        
        # Load product data
        self.products_data = self._load_products_data()
        
        # Ensure output directory exists
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "tibco_cases"))
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized TibcoCaseManager with output directory: {self.output_dir}")
    
    def _check_curl_available(self) -> bool:
        """Check if curl command is available on the system"""
        try:
            # Use 'where' on Windows, 'which' on Unix/Linux
            if os.name == 'nt':  # Windows
                result = subprocess.run(["where", "curl"], capture_output=True, text=True)
            else:  # Unix/Linux
                result = subprocess.run(["which", "curl"], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception:
            return False
    
    def _load_products_data(self) -> Dict[str, Any]:
        """Load product data from JSON file"""
        products_file = Path(__file__).parent / "products.json"
        try:
            if products_file.exists():
                with open(products_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Products file not found: {products_file}")
                return {"status": "error", "data": []}
        except Exception as e:
            logger.error(f"Error loading products data: {e}")
            return {"status": "error", "data": []}
    
    def get_product_id(self, product_name: str) -> Optional[int]:
        """Get product ID by name (case-insensitive partial match)"""
        if not product_name or not self.products_data or "data" not in self.products_data:
            return None
        
        product_name_lower = product_name.lower()
        
        # Try exact match on subCategoryName first
        for product in self.products_data["data"]:
            if product.get("subCategoryName", "").lower() == product_name_lower:
                return product.get("subCategoryId")
        
        # Try partial match on subCategoryName
        for product in self.products_data["data"]:
            if product_name_lower in product.get("subCategoryName", "").lower():
                return product.get("subCategoryId")
        
        # Try match on categoryName
        for product in self.products_data["data"]:
            if product_name_lower in product.get("categoryName", "").lower():
                return product.get("subCategoryId")
        
        return None
    
    def list_available_products(self) -> None:
        """Print a list of available products"""
        if not self.products_data or "data" not in self.products_data:
            print("No product data available.")
            return
        
        products = self.products_data["data"]
        
        print("\n" + "="*100)
        print(f"{'ID':<8} {'CATEGORY NAME':<25} {'SUBCATEGORY NAME':<50}")
        print("="*100)
        
        for product in sorted(products, key=lambda x: x.get("subCategoryName", "")):
            print(f"{product.get('subCategoryId', ''):<8} {product.get('categoryName', ''):<25} {product.get('subCategoryName', ''):<50}")
        
        print("="*100)
        print(f"Total products: {len(products)}\n")
    
    def _validate_cookies(self) -> bool:
        """Validate that required cookies are present"""
        required_cookies = ["opentoken", "opentoken-legacy", "csg-csm-d-zz-a-support"]
        missing_cookies = []
        
        for cookie_name in required_cookies:
            if not self.cookies.get(cookie_name):
                missing_cookies.append(cookie_name)
        
        if missing_cookies:
            logger.error(f"Missing required cookies: {missing_cookies}")
            logger.error("Please set these as environment variables (uppercase, replace - with _)")
            return False
        
        return True
    
    def search_cases_curl(self, search_query: str = "BW CE", product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for cases using curl (exact command as provided)
        """
        logger.info(f"Searching for cases with query: {search_query}")
        if product_id:
            logger.info(f"Filtering by product ID: {product_id}")
        
        # Prepare the form data
        form_data = {
            "searchQuery": search_query,
            "sourcesArray": ["Requests"],
            "sortByFieldsArray": [{"createdTimestamp": {"order": "desc"}}],
            "resultFrom": 0,
            "resultSize": 100,
            "searchedLocation": "KB_SEARCH",
            "searchOperator": "AND"
        }
        
        # Add product filter if provided
        if product_id:
            form_data["filterDataArray"] = [{"filterName": "subCategoryIds", "filterValues": [product_id]}]
        else:
            form_data["filterDataArray"] = []
        
        # If curl is not available, use requests instead
        if not self.curl_available:
            return self._search_cases_requests(search_query, form_data)
            
        # Build curl command
        curl_cmd = [
            "curl", self.search_url,
            "-H", "accept: application/json, text/plain, */*",
            "-H", "accept-language: en-US,en;q=0.9",
            "-H", "content-type: multipart/form-data; boundary=----WebKitFormBoundaryGpq0p9AtABk9ksjE",
            "-H", f"origin: https://support.tibco.com",
            "-H", "priority: u=1, i",
            "-H", "referer: https://support.tibco.com/",
            "-H", 'sec-ch-ua: "Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "-H", "sec-ch-ua-mobile: ?0",
            "-H", 'sec-ch-ua-platform: "Unknown"',
            "-H", "sec-fetch-dest: empty",
            "-H", "sec-fetch-mode: cors",
            "-H", "sec-fetch-site: same-site",
            "-H", "sec-gpc: 1",
            "-H", f"user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        ]
        
        # Add cookies
        cookie_string = "; ".join([f"{k}={v}" for k, v in self.cookies.items() if v])
        curl_cmd.extend(["-b", cookie_string])
        
        # Prepare multipart form data
        boundary = "------WebKitFormBoundaryGpq0p9AtABk9ksjE"
        data = f"{boundary}\r\n"
        data += 'Content-Disposition: form-data; name="data"\r\n\r\n'
        data += json.dumps(form_data)
        data += f"\r\n{boundary}--\r\n"
        
        curl_cmd.extend(["--data-raw", data])
        
        try:
            # Execute curl command
            logger.debug(f"Executing curl command")
            result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
            
            # Parse JSON response
            response_data = json.loads(result.stdout)
            logger.info(f"Search completed successfully")
            
            # Log some statistics
            if "data" in response_data and "kbdocs" in response_data["data"]:
                cases = response_data["data"]["kbdocs"][0]["dataArray"]
                logger.info(f"Found {len(cases)} cases")
            
            return response_data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl command failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {result.stdout[:500]}...")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise
    
    def _search_cases_requests(self, search_query: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for cases using the requests library (alternative to curl)
        """
        logger.info(f"Searching for cases with requests: {search_query}")
        
        try:
            # Prepare multipart form data
            files = {
                'data': (None, json.dumps(form_data), 'application/json')
            }
            
            # Make request
            response = requests.post(
                self.search_url,
                headers={
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "en-US,en;q=0.9",
                    "origin": "https://support.tibco.com",
                    "referer": "https://support.tibco.com/",
                    "user-agent": self.headers["user-agent"]
                },
                cookies=self.cookies,
                files=files,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse JSON response
            response_data = response.json()
            logger.info(f"Search completed successfully")
            
            # Log some statistics
            if "data" in response_data and "kbdocs" in response_data["data"]:
                cases = response_data["data"]["kbdocs"][0]["dataArray"]
                logger.info(f"Found {len(cases)} cases")
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise
    
    def download_pdf_curl(self, request_id: str, output_filename: Optional[str] = None) -> Path:
        """
        Download a PDF using curl (exact command as provided)
        """
        logger.info(f"Downloading PDF for case ID: {request_id}")
        
        pdf_url = self.pdf_url_template.format(request_id=request_id)
        
        if not output_filename:
            output_filename = f"case_{request_id}.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Build curl command
        curl_cmd = [
            "curl", pdf_url,
            "-o", str(output_path)
        ]
        
        # Add headers
        for header, value in self.headers.items():
            curl_cmd.extend(["-H", f"{header}: {value}"])
        
        # Add cookies
        cookie_string = "; ".join([f"{k}={v}" for k, v in self.cookies.items() if v])
        curl_cmd.extend(["-b", cookie_string])
        
        try:
            # Execute curl command
            logger.debug(f"Executing curl command for PDF download")
            result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
            
            # Verify file was created
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully downloaded PDF: {output_path}")
                return output_path
            else:
                raise Exception(f"PDF file not created or is empty: {output_path}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl command failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PDF download: {e}")
            raise
    
    def download_pdf_requests(self, request_id: str, output_filename: Optional[str] = None) -> Path:
        """
        Download a PDF using requests library (alternative method)
        """
        logger.info(f"Downloading PDF for case ID: {request_id} using requests")
        
        pdf_url = self.pdf_url_template.format(request_id=request_id)
        
        if not output_filename:
            output_filename = f"case_{request_id}.pdf"
        
        output_path = self.output_dir / output_filename
        
        try:
            # Prepare cookies for requests
            cookies_dict = {k: v for k, v in self.cookies.items() if v}
            
            # Make request
            response = requests.get(
                pdf_url,
                headers=self.headers,
                cookies=cookies_dict,
                stream=True,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded PDF: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during PDF download: {e}")
            raise
    
    def process_search_results(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process search results and return list of case data
        """
        case_data_list = []
        
        try:
            if "data" in search_results and "kbdocs" in search_results["data"]:
                cases = search_results["data"]["kbdocs"][0]["dataArray"]
                
                for case in cases:
                    request_id = case.get("requestId")
                    title = case.get("title", "No title")
                    status = case.get("status", "Unknown")
                    created_date = case.get("createdDate", "Unknown")
                    
                    if request_id:
                        case_data = {
                            "request_id": str(request_id),
                            "title": title,
                            "status": status,
                            "created_date": created_date
                        }
                        case_data_list.append(case_data)
                        logger.debug(f"Found case ID: {request_id} - {title}")
                
                logger.info(f"Extracted {len(case_data_list)} case records")
            else:
                logger.warning("No cases found in search results")
        
        except Exception as e:
            logger.error(f"Error processing search results: {e}")
            raise
        
        return case_data_list
    
    def print_case_list(self, case_data_list: List[Dict[str, Any]]):
        """
        Print case list in a nice format
        """
        if not case_data_list:
            print("No cases found.")
            return
        
        print("\n" + "="*100)
        print(f"{'REQUEST ID':<15} {'STATUS':<15} {'CREATED DATE':<20} {'TITLE':<50}")
        print("="*100)
        
        for case in case_data_list:
            print(f"{case['request_id']:<15} {case['status']:<15} {case['created_date']:<20} {case['title'][:50]}")
        
        print("="*100)
        print(f"Total cases: {len(case_data_list)}\n")
    
    def extract_case_ids(self, case_data_list: List[Dict[str, Any]]) -> List[str]:
        """
        Extract just the case IDs from case data list
        """
        return [case["request_id"] for case in case_data_list]
    
    def list_cases(self, search_query: str = "BW CE", product_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for cases and list them
        """
        if not self._validate_cookies():
            raise ValueError("Missing required cookies. Please check your .env file")
        
        # Get product ID if product name is provided
        product_id = None
        if product_name:
            product_id = self.get_product_id(product_name)
            if product_id is None:
                raise ValueError(f"Product not found: {product_name}")
            print(f"Filtering by product: {product_name} (ID: {product_id})")
        
        # Search for cases
        search_results = self.search_cases_curl(search_query, product_id)
        
        # Process results
        case_data_list = self.process_search_results(search_results)
        
        # Print the list
        self.print_case_list(case_data_list)
        
        return case_data_list
    
    def download_cases(self, case_data_list: List[Dict[str, Any]], limit: Optional[int] = None, use_curl: bool = True) -> List[Path]:
        """
        Download PDFs for the specified cases, optionally limited to a certain number
        """
        downloaded_files = []
        
        if not case_data_list:
            logger.warning("No cases to download")
            return downloaded_files
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            case_data_list = case_data_list[:limit]
            logger.info(f"Limiting download to {limit} cases")
        
        # Extract case IDs
        case_ids = self.extract_case_ids(case_data_list)
        
        # Download PDFs
        logger.info(f"Starting download of {len(case_ids)} PDFs")
        
        # If curl is not available, force use_curl to False
        if use_curl and not self.curl_available:
            logger.warning("Curl not available, using requests instead")
            use_curl = False
        
        for i, case_id in enumerate(case_ids, 1):
            try:
                print(f"Downloading {i}/{len(case_ids)}: Case {case_id}")
                
                if use_curl:
                    output_path = self.download_pdf_curl(case_id)
                else:
                    output_path = self.download_pdf_requests(case_id)
                
                downloaded_files.append(output_path)
                
                # Small delay to avoid overwhelming the server
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to download case {case_id}: {e}")
                print(f"Error: Failed to download case {case_id}")
                # Continue with next case
                continue
        
        if downloaded_files:
            print("\nDownload Summary:")
            print(f"Total files downloaded: {len(downloaded_files)}")
            print(f"Files saved to: {self.output_dir}")
            print("\nDownloaded files:")
            for file in downloaded_files:
                print(f"  - {file.name}")
        else:
            print("\nNo files were downloaded successfully.")
        
        return downloaded_files
    
    def search_and_download_all(self, search_query: str = "BW CE", product_name: Optional[str] = None, use_curl: bool = True) -> List[Path]:
        """
        Search for cases and download all PDFs
        """
        if not self._validate_cookies():
            raise ValueError("Missing required cookies. Please check your .env file")
        
        downloaded_files = []
        
        try:
            # Get product ID if product name is provided
            product_id = None
            if product_name:
                product_id = self.get_product_id(product_name)
                if product_id is None:
                    raise ValueError(f"Product not found: {product_name}")
                print(f"Filtering by product: {product_name} (ID: {product_id})")
            
            # Search for cases
            search_results = self.search_cases_curl(search_query, product_id)
            
            # Process results
            case_data_list = self.process_search_results(search_results)
            
            # Download PDFs
            downloaded_files = self.download_cases(case_data_list, use_curl=use_curl)
            
        except Exception as e:
            logger.error(f"Error in search_and_download_all: {e}")
            raise
        
        return downloaded_files


def main():
    """Main entry point"""
    # Get the script name dynamically
    script_name = os.path.basename(sys.argv[0])
    
    # Custom formatter for better help formatting
    class RawDescriptionArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, 
                                                     argparse.RawDescriptionHelpFormatter):
        pass
    
    # Create the top-level parser with program description
    program_description = f"""
TIBCO Support Case Manager
==========================
A tool to search for and download TIBCO support case PDFs.

This utility helps you:
- Search for support cases using keywords
- Filter cases by product
- Download case PDFs in bulk or selectively
- List all available TIBCO products

The tool requires TIBCO support portal cookies to be set as environment variables:
- OPENTOKEN
- OPENTOKEN_LEGACY
- CSG_TOKEN

Environment variables can be set in a .env file in the same directory.
You can use the create_env.py utility to generate the .env file from a curl command:
  python create_env.py command.txt

Examples:
---------
List all cases:
  python {script_name} list

List cases for a specific product:
  python {script_name} list --product "BusinessWorks"

Search for specific keywords:
  python {script_name} list --query "connection error"

Download the first 5 cases:
  python {script_name} download

Download all matching cases:
  python {script_name} download --all

Download cases for a specific product:
  python {script_name} download --product "BusinessEvents" --limit 10

List available products:
  python {script_name} products
"""
    
    parser = argparse.ArgumentParser(
        description=program_description,
        formatter_class=RawDescriptionArgumentDefaultsHelpFormatter,
        epilog="For more information, check the GitHub repository."
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser(
        "list", 
        help="List cases matching the criteria",
        description="Search for and list TIBCO support cases.",
        formatter_class=RawDescriptionArgumentDefaultsHelpFormatter,
        epilog=textwrap.dedent(f"""
        Examples:
          python {script_name} list
          python {script_name} list --query "connection error"
          python {script_name} list --product "BusinessWorks"
        """)
    )
    list_parser.add_argument(
        "--query", "-q", 
        default=os.getenv("SEARCH_QUERY", "BW CE"),
        help="Search query (keywords to look for in case descriptions)"
    )
    list_parser.add_argument(
        "--product", "-p", 
        help="Filter by product name (can be partial match)"
    )
    
    # Download command
    download_parser = subparsers.add_parser(
        "download", 
        help="Download case PDFs",
        description="Search for and download TIBCO support case PDFs.",
        formatter_class=RawDescriptionArgumentDefaultsHelpFormatter,
        epilog=textwrap.dedent(f"""
        Examples:
          python {script_name} download
          python {script_name} download --all
          python {script_name} download --limit 10
          python {script_name} download --product "BusinessEvents"
          python {script_name} download --query "error" --product "BusinessWorks" --limit 5
        """)
    )
    download_parser.add_argument(
        "--query", "-q", 
        default=os.getenv("SEARCH_QUERY", "BW CE"),
        help="Search query (keywords to look for in case descriptions)"
    )
    download_parser.add_argument(
        "--product", "-p", 
        help="Filter by product name (can be partial match)"
    )
    download_parser.add_argument(
        "--limit", "-l", 
        type=int, 
        default=5,
        help="Limit the number of cases to download (default: 5, use --all to download all)"
    )
    download_parser.add_argument(
        "--all", "-a", 
        action="store_true",
        help="Download all matching cases (overrides --limit)"
    )
    download_parser.add_argument(
        "--use-requests", 
        action="store_true", 
        help="Use Python requests library instead of curl"
    )
    
    # Products command
    products_parser = subparsers.add_parser(
        "products", 
        help="List available TIBCO products",
        description="Display a list of all TIBCO products available for filtering.",
        formatter_class=RawDescriptionArgumentDefaultsHelpFormatter,
        epilog=f"Use the product names with the --product option in list or download commands."
    )
    
    # Setup parser
    setup_parser = subparsers.add_parser(
        "setup", 
        help="Check authentication setup",
        description="Verify your authentication setup for TIBCO Support Portal.",
        formatter_class=RawDescriptionArgumentDefaultsHelpFormatter,
        epilog=textwrap.dedent("""
        This command checks if the required cookies are set in environment variables.
        Required cookies:
          - OPENTOKEN
          - OPENTOKEN_LEGACY
          - CSG_TOKEN
        
        You can set these in a .env file in the same directory.
        """)
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default command if none provided
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Create manager instance
        manager = TibcoCaseManager()
        
        # Process commands
        if args.command == "setup":
            print("\nChecking TIBCO Support Portal authentication...")
            if manager._validate_cookies():
                print("✅ Authentication setup is valid! All required cookies are present.")
                print("\nYou can now use the other commands to search for and download cases.")
            else:
                print("❌ Authentication setup is invalid. Missing required cookies.")
                print("\nYou need to set the following environment variables:")
                print("  - OPENTOKEN")
                print("  - OPENTOKEN_LEGACY")
                print("  - CSG_TOKEN")
                print("\nYou can set these in a .env file in the same directory.")
                print("These cookie values can be obtained from your browser after logging into the TIBCO Support Portal.")
                
        elif args.command == "products":
            print("\nListing available TIBCO products:")
            manager.list_available_products()
            
        elif args.command == "list":
            print(f"\nListing TIBCO Support Cases for query: '{args.query}'")
            manager.list_cases(args.query, args.product)
            
        elif args.command == "download":
            use_curl = not args.use_requests
            print(f"\nSearching TIBCO Support Cases for query: '{args.query}'")
            
            # First list the cases
            case_data_list = manager.list_cases(args.query, args.product)
            
            if not case_data_list:
                print("No cases found to download.")
                sys.exit(0)
            
            # Check which download mode to use
            if args.all:
                print(f"\nDownloading ALL {len(case_data_list)} cases...")
                limit = None
            else:
                limit = args.limit
                print(f"\nDownloading first {limit} cases...")
            
            # Download cases
            manager.download_cases(case_data_list, limit=limit, use_curl=use_curl)
    
    except ValueError as e:
        logger.error(f"Value error: {e}")
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()