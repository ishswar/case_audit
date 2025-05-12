#!/usr/bin/env python3
"""
Script to clean up duplicate case entries in the all_jobs.json file.
This keeps only one entry per case number, removing any duplicates.
"""

import os
import json
import sys

def clean_jobs_file(jobs_file):
    print(f"Loading jobs file: {jobs_file}")
    
    # Load the jobs
    try:
        with open(jobs_file, 'r') as f:
            jobs = json.load(f)
    except Exception as e:
        print(f"Error loading jobs file: {e}")
        return 1
    
    print(f"Loaded {len(jobs)} jobs")
    
    # Track jobs by case number
    case_to_job_map = {}
    jobs_to_remove = []
    
    # First pass: find the first entry for each case number
    for job_id, job_info in jobs.items():
        if "case_number" in job_info:
            case_number = job_info["case_number"]
            if case_number not in case_to_job_map:
                case_to_job_map[case_number] = job_id
            else:
                # This is a duplicate entry
                jobs_to_remove.append(job_id)
    
    # Second pass: remove duplicates
    for job_id in jobs_to_remove:
        if job_id in jobs:
            print(f"Removing duplicate entry: {job_id}")
            del jobs[job_id]
    
    # Save the cleaned jobs file
    if jobs_to_remove:
        print(f"Removed {len(jobs_to_remove)} duplicate entries")
        try:
            # Make a backup first
            backup_file = jobs_file + ".bak"
            with open(backup_file, 'w') as f:
                json.dump(jobs, f, indent=2)
            print(f"Created backup at: {backup_file}")
            
            # Save the cleaned file
            with open(jobs_file, 'w') as f:
                json.dump(jobs, f, indent=2)
            print(f"Saved cleaned jobs file with {len(jobs)} jobs")
        except Exception as e:
            print(f"Error saving jobs file: {e}")
            return 1
    else:
        print("No duplicate entries found")
    
    return 0

def main():
    # Determine the jobs file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_dir = os.path.join(script_dir, "jobs")
    jobs_file = os.path.join(jobs_dir, "all_jobs.json")
    
    if not os.path.exists(jobs_file):
        print(f"Error: Jobs file not found at {jobs_file}")
        return 1
    
    print("TIBCO Case Audit Jobs Cleanup")
    print("=============================")
    print("This tool will clean up the all_jobs.json file by:")
    print("1. Keeping only one entry per case number")
    print("2. Creating a backup of the original file")
    print()
    print(f"Jobs file: {jobs_file}")
    
    confirmation = input("Do you want to proceed? (y/n): ").strip().lower()
    if confirmation != 'y':
        print("Operation cancelled")
        return 0
    
    return clean_jobs_file(jobs_file)

if __name__ == "__main__":
    sys.exit(main()) 