#!/usr/bin/env python3
"""
Round 1 Task Generator

This script reads submissions from a CSV file and generates round 1 tasks for students.
It sends task requests to student endpoints and logs the results.
"""

import csv
import json
import uuid
import hashlib
import random
import requests
import time
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the database directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
from database import DatabaseManager

class TaskTemplates:
    """Task templates for different types of applications"""
    
    @staticmethod
    def get_templates():
        return {
            'captcha-solver': {
                'round1': {
                    'brief': "Create a captcha solver that handles ?url=https://.../image.png. Default to attached sample. Display the solved captcha text within 15 seconds.",
                    'checks': [
                        "Repo has MIT license",
                        "README.md is professional",
                        "Page displays captcha URL passed at ?url=...",
                        "Page displays solved captcha text within 15 seconds",
                        "Code is well-commented and organized"
                    ],
                    'attachments': [
                        {
                            'name': 'sample.png',
                            'url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
                        }
                    ]
                },
                'round2': {
                    'brief': "Enhance the captcha solver to handle SVG images and implement audio captcha support.",
                    'checks': [
                        "SVG captcha support implemented",
                        "Audio captcha functionality added",
                        "Error handling for unsupported formats",
                        "Updated README with new features",
                        "Backward compatibility maintained"
                    ]
                }
            },
            'weather-dashboard': {
                'round1': {
                    'brief': "Create a weather dashboard that displays current weather for a city passed as ?city=CityName. Use OpenWeatherMap API or similar.",
                    'checks': [
                        "Repo has MIT license",
                        "README.md is professional",
                        "Page accepts city parameter from URL",
                        "Displays current weather information",
                        "Responsive design for mobile devices"
                    ]
                },
                'round2': {
                    'brief': "Add 7-day weather forecast and implement location-based weather detection using geolocation API.",
                    'checks': [
                        "7-day forecast implemented",
                        "Geolocation API integration",
                        "Weather maps or charts added",
                        "Error handling for API failures",
                        "Performance optimizations"
                    ]
                }
            },
            'todo-manager': {
                'round1': {
                    'brief': "Create a todo manager that supports adding, editing, deleting, and marking tasks as complete. Use localStorage for persistence.",
                    'checks': [
                        "Repo has MIT license",
                        "README.md is professional",
                        "Add, edit, delete functionality works",
                        "Mark tasks as complete/incomplete",
                        "Data persists using localStorage"
                    ]
                },
                'round2': {
                    'brief': "Add categories, due dates, priority levels, and implement search/filter functionality.",
                    'checks': [
                        "Categories system implemented",
                        "Due dates and priority levels",
                        "Search and filter functionality",
                        "Export/import capabilities",
                        "Enhanced UI/UX design"
                    ]
                }
            }
        }

class Round1TaskGenerator:
    def __init__(self, evaluation_url, db_path=None):
        self.evaluation_url = evaluation_url
        self.db = DatabaseManager(db_path or 'evaluation.db')
        self.templates = TaskTemplates.get_templates()
    
    def generate_task_id(self, template_id, brief, attachments):
        """Generate a unique task ID based on template and content"""
        content = f"{brief}{json.dumps(attachments or [])}"
        hash_value = hashlib.md5(content.encode()).hexdigest()[:5]
        return f"{template_id}-{hash_value}"
    
    def select_template(self, email, date_hour):
        """Select a template based on email and date for deterministic randomness"""
        seed = hashlib.md5(f"{email}{date_hour}".encode()).hexdigest()
        random.seed(seed)
        
        template_ids = list(self.templates.keys())
        selected_id = random.choice(template_ids)
        
        return selected_id, self.templates[selected_id]
    
    def generate_task(self, email, endpoint, secret):
        """Generate a round 1 task for a student"""
        try:
            # Use current hour for template selection
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            # Select template
            template_id, template = self.select_template(email, current_hour)
            round1_template = template['round1']
            
            # Generate task data
            task_id = self.generate_task_id(template_id, round1_template['brief'], 
                                          round1_template.get('attachments'))
            nonce = str(uuid.uuid4())
            
            task_data = {
                'email': email,
                'secret': secret,
                'task': task_id,
                'round': 1,
                'nonce': nonce,
                'brief': round1_template['brief'],
                'checks': round1_template['checks'],
                'evaluation_url': self.evaluation_url,
                'attachments': round1_template.get('attachments', [])
            }
            
            return task_data
            
        except Exception as e:
            print(f"Error generating task for {email}: {e}")
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
            
            print(f"Sent task to {endpoint}: HTTP {response.status_code}")
            return response.status_code
            
        except Exception as e:
            print(f"Error sending task to {endpoint}: {e}")
            return None
    
    def process_submissions(self, submissions_file):
        """Process all submissions and generate round 1 tasks"""
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            with open(submissions_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    email = row['email'].strip()
                    endpoint = row['endpoint'].strip()
                    secret = row['secret'].strip()
                    
                    print(f"\nProcessing submission for {email}")
                    
                    # Check if round 1 task already exists
                    if self.db.task_exists(email, None, 1):  # Check any round 1 task for this email
                        print(f"Skipping {email}: Round 1 task already exists")
                        skipped_count += 1
                        continue
                    
                    # Generate task
                    task_data = self.generate_task(email, endpoint, secret)
                    if not task_data:
                        print(f"Error generating task for {email}")
                        error_count += 1
                        continue
                    
                    # Send task to student endpoint
                    status_code = self.send_task(endpoint, task_data)
                    
                    # Log task to database
                    task_record = task_data.copy()
                    task_record['endpoint'] = endpoint
                    task_record['statuscode'] = status_code
                    
                    success = self.db.insert_task(task_record)
                    
                    if success:
                        print(f"Successfully processed {email}")
                        processed_count += 1
                    else:
                        print(f"Error logging task for {email}")
                        error_count += 1
                    
                    # Brief delay between requests
                    time.sleep(1)
        
        except FileNotFoundError:
            print(f"Error: Submissions file '{submissions_file}' not found")
            return
        except Exception as e:
            print(f"Error processing submissions: {e}")
            return
        
        print(f"\n=== Round 1 Processing Complete ===")
        print(f"Processed: {processed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors: {error_count}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and send Round 1 tasks to students')
    parser.add_argument('--submissions', required=True, 
                       help='Path to submissions CSV file')
    parser.add_argument('--evaluation-url', required=True,
                       help='URL of the evaluation API endpoint')
    parser.add_argument('--db-path', 
                       help='Path to database file (default: evaluation.db)')
    
    args = parser.parse_args()
    
    # Initialize task generator
    generator = Round1TaskGenerator(args.evaluation_url, args.db_path)
    
    print("=== Round 1 Task Generator ===")
    print(f"Submissions file: {args.submissions}")
    print(f"Evaluation URL: {args.evaluation_url}")
    print(f"Database: {args.db_path or 'evaluation.db'}")
    print()
    
    # Process submissions
    generator.process_submissions(args.submissions)

if __name__ == "__main__":
    main()