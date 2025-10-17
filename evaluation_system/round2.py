#!/usr/bin/env python3
"""
Round 2 Task Generator

This script generates round 2 tasks for students who have completed round 1.
It sends modification/enhancement requests to student endpoints.
"""

import json
import uuid
import hashlib
import random
import requests
import time
import os
import sys
from datetime import datetime

# Add the database directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
from database import DatabaseManager

class Round2TaskGenerator:
    def __init__(self, evaluation_url, db_path=None):
        self.evaluation_url = evaluation_url
        self.db = DatabaseManager(db_path or 'evaluation.db')
        
        # Round 2 templates based on original tasks
        self.round2_templates = {
            'captcha-solver': [
                {
                    'brief': "Enhance the captcha solver to handle SVG images and implement audio captcha support with text-to-speech output.",
                    'checks': [
                        "SVG captcha support implemented",
                        "Audio captcha functionality added",
                        "Text-to-speech output for solved captchas",
                        "Error handling for unsupported formats",
                        "Updated README with new features",
                        "Backward compatibility maintained"
                    ]
                },
                {
                    'brief': "Add batch processing capability to solve multiple captchas from a comma-separated URL list and display results in a table.",
                    'checks': [
                        "Batch processing of multiple URLs",
                        "Results displayed in organized table",
                        "Progress indicators during processing",
                        "Export functionality for results",
                        "Error handling for invalid URLs",
                        "Performance optimizations"
                    ]
                }
            ],
            'weather-dashboard': [
                {
                    'brief': "Add 7-day weather forecast, implement location-based weather detection using geolocation API, and add weather maps.",
                    'checks': [
                        "7-day forecast implemented",
                        "Geolocation API integration",
                        "Weather maps or charts added",
                        "Temperature unit conversion (C/F)",
                        "Error handling for API failures",
                        "Responsive design improvements"
                    ]
                },
                {
                    'brief': "Implement weather alerts, historical data comparison, and add multiple city comparison dashboard.",
                    'checks': [
                        "Weather alerts and notifications",
                        "Historical weather data display",
                        "Multi-city comparison view",
                        "Favorite cities functionality",
                        "Data caching for performance",
                        "Enhanced mobile experience"
                    ]
                }
            ],
            'todo-manager': [
                {
                    'brief': "Add categories, due dates, priority levels, and implement search/filter functionality with data export capabilities.",
                    'checks': [
                        "Categories system implemented",
                        "Due dates and priority levels",
                        "Search and filter functionality",
                        "Export/import capabilities (JSON/CSV)",
                        "Task sorting options",
                        "Enhanced UI/UX design"
                    ]
                },
                {
                    'brief': "Implement collaborative features with task sharing, comments, and real-time updates using localStorage or API.",
                    'checks': [
                        "Task sharing functionality",
                        "Comments and notes system",
                        "Real-time updates simulation",
                        "User roles and permissions",
                        "Activity history tracking",
                        "Notification system"
                    ]
                }
            ]
        }
    
    def extract_task_type(self, task_id):
        """Extract task type from task ID"""
        return task_id.split('-')[0] if '-' in task_id else task_id
    
    def generate_round2_task(self, repo_data, original_task_data):
        """Generate a round 2 task based on the original round 1 task"""
        try:
            task_type = self.extract_task_type(original_task_data['task'])
            
            if task_type not in self.round2_templates:
                print(f"No round 2 template found for task type: {task_type}")
                return None
            
            # Select a random round 2 template for this task type
            templates = self.round2_templates[task_type]
            selected_template = random.choice(templates)
            
            # Generate new task data
            nonce = str(uuid.uuid4())
            
            task_data = {
                'email': repo_data['email'],
                'secret': original_task_data['secret'],
                'task': original_task_data['task'],  # Keep same task ID
                'round': 2,
                'nonce': nonce,
                'brief': selected_template['brief'],
                'checks': selected_template['checks'],
                'evaluation_url': self.evaluation_url,
                'attachments': []  # Round 2 typically doesn't need new attachments
            }
            
            return task_data
            
        except Exception as e:
            print(f"Error generating round 2 task: {e}")
            return None
    
    def send_task(self, endpoint, task_data):
        """Send task to student endpoint"""
        try:
            response = requests.post(
                endpoint,
                headers={'Content-Type': 'application/json'},
                json=task_data,
                timeout=30
            )
            
            print(f"Sent round 2 task to {endpoint}: HTTP {response.status_code}")
            return response.status_code
            
        except Exception as e:
            print(f"Error sending round 2 task to {endpoint}: {e}")
            return None
    
    def process_round1_completions(self):
        """Process all round 1 completions and generate round 2 tasks"""
        # Get all round 1 repo submissions
        round1_repos = self.db.get_repos(round_num=1)
        
        if not round1_repos:
            print("No round 1 repositories found")
            return
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for repo in round1_repos:
            email = repo['email']
            task = repo['task']
            
            print(f"\nProcessing round 2 for {email} - {task}")
            
            # Check if round 2 task already exists
            if self.db.task_exists(email, task, 2):
                print(f"Skipping {email}: Round 2 task already exists for {task}")
                skipped_count += 1
                continue
            
            # Get original round 1 task data
            round1_tasks = self.db.get_tasks(email=email, round_num=1)
            original_task = None
            
            for task_record in round1_tasks:
                if task_record['task'] == task:
                    original_task = task_record
                    break
            
            if not original_task:
                print(f"Error: Could not find original round 1 task for {email} - {task}")
                error_count += 1
                continue
            
            # Generate round 2 task
            round2_task = self.generate_round2_task(repo, original_task)
            if not round2_task:
                print(f"Error generating round 2 task for {email}")
                error_count += 1
                continue
            
            # Send task to student endpoint
            endpoint = original_task['endpoint']
            status_code = self.send_task(endpoint, round2_task)
            
            # Log task to database
            task_record = round2_task.copy()
            task_record['endpoint'] = endpoint
            task_record['statuscode'] = status_code
            
            success = self.db.insert_task(task_record)
            
            if success:
                print(f"Successfully processed round 2 for {email}")
                processed_count += 1
            else:
                print(f"Error logging round 2 task for {email}")
                error_count += 1
            
            # Brief delay between requests
            time.sleep(1)
        
        print(f"\n=== Round 2 Processing Complete ===")
        print(f"Processed: {processed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors: {error_count}")
    
    def retry_failed_round2_tasks(self, max_retries=3):
        """Retry sending round 2 tasks that failed"""
        failed_tasks = []
        
        # Get round 2 tasks with non-200 status codes
        all_round2_tasks = self.db.get_tasks(round_num=2)
        
        for task in all_round2_tasks:
            if task['statuscode'] != 200:
                failed_tasks.append(task)
        
        if not failed_tasks:
            print("No failed round 2 tasks to retry")
            return
        
        print(f"Found {len(failed_tasks)} failed round 2 tasks to retry")
        
        retry_count = 0
        
        for task in failed_tasks:
            print(f"\nRetrying round 2 task for {task['email']} - {task['task']}")
            
            # Prepare task data
            task_data = {
                'email': task['email'],
                'secret': task['secret'],
                'task': task['task'],
                'round': task['round'],
                'nonce': task['nonce'],
                'brief': task['brief'],
                'checks': json.loads(task['checks']) if task['checks'] else [],
                'evaluation_url': task['evaluation_url'],
                'attachments': json.loads(task['attachments']) if task['attachments'] else []
            }
            
            # Send task
            status_code = self.send_task(task['endpoint'], task_data)
            
            if status_code == 200:
                # Update task record with new status code
                # Note: This would require an update method in DatabaseManager
                print(f"Successfully retried round 2 task for {task['email']}")
                retry_count += 1
            else:
                print(f"Retry failed for {task['email']}")
            
            time.sleep(2)  # Longer delay for retries
        
        print(f"\n=== Round 2 Retry Complete ===")
        print(f"Successfully retried: {retry_count}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and send Round 2 tasks to students')
    parser.add_argument('--evaluation-url', required=True,
                       help='URL of the evaluation API endpoint')
    parser.add_argument('--db-path', 
                       help='Path to database file (default: evaluation.db)')
    parser.add_argument('--retry-failed', action='store_true',
                       help='Retry failed round 2 tasks instead of generating new ones')
    
    args = parser.parse_args()
    
    # Initialize task generator
    generator = Round2TaskGenerator(args.evaluation_url, args.db_path)
    
    print("=== Round 2 Task Generator ===")
    print(f"Evaluation URL: {args.evaluation_url}")
    print(f"Database: {args.db_path or 'evaluation.db'}")
    print()
    
    if args.retry_failed:
        # Retry failed round 2 tasks
        generator.retry_failed_round2_tasks()
    else:
        # Process round 1 completions and generate round 2 tasks
        generator.process_round1_completions()

if __name__ == "__main__":
    main()