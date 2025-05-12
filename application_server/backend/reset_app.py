#!/usr/bin/env python3
"""
Script to reset the application state by clearing the processed case numbers
and optionally removing all jobs.

This is useful when you want to start fresh or when you're experiencing
duplicate entry issues.
"""

import os
import sys
import json
import requests

def reset_app_via_api():
    """Reset the app by calling the admin API endpoint"""
    try:
        api_url = "http://localhost:8000/admin/reset"
        params = {"clear_jobs": True}  # Set to True to also clear all jobs
        
        print("Calling reset API endpoint...")
        response = requests.post(api_url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! {result['message']}")
            return 0
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return 1
    except Exception as e:
        print(f"Error connecting to API: {e}")
        print("Is the backend server running?")
        return 1

def reset_app_manually():
    """Reset the app by directly modifying the jobs file"""
    # Determine the jobs file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_dir = os.path.join(script_dir, "jobs")
    jobs_file = os.path.join(jobs_dir, "all_jobs.json")
    
    if not os.path.exists(jobs_file):
        print(f"Error: Jobs file not found at {jobs_file}")
        return 1
    
    print(f"Creating empty jobs file at: {jobs_file}")
    
    try:
        # Make a backup first
        backup_file = jobs_file + ".bak"
        if os.path.exists(jobs_file):
            with open(jobs_file, 'r') as src:
                with open(backup_file, 'w') as dst:
                    dst.write(src.read())
            print(f"Created backup at: {backup_file}")
        
        # Create an empty jobs file
        with open(jobs_file, 'w') as f:
            f.write("{}\n")
        print("Successfully reset the application state")
        print("Note: You'll need to restart the backend server for changes to take effect")
        return 0
    except Exception as e:
        print(f"Error resetting application: {e}")
        return 1

def main():
    """Main function"""
    print("TIBCO Case Audit Application Reset Tool")
    print("=======================================")
    print("This tool will reset the application state by:")
    print("1. Clearing the list of processed case numbers")
    print("2. Optionally removing all job entries")
    print()
    print("Choose reset method:")
    print("1. Reset via API (backend server must be running)")
    print("2. Reset manually (will create empty jobs file)")
    print("3. Cancel")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            return reset_app_via_api()
        elif choice == "2":
            return reset_app_manually()
        elif choice == "3":
            print("Operation cancelled")
            return 0
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 