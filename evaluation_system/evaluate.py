#!/usr/bin/env python3
"""
Evaluation Script

This script evaluates submitted repositories based on various checks:
- Repository-level rule-based checks
- LLM-based static checks
- Dynamic checks using Playwright
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile
import shutil

# Add the database directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
from database import DatabaseManager

try:
    import openai
except ImportError:
    openai = None
    print("Warning: OpenAI not available, LLM checks will be skipped")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    print("Warning: Playwright not available, dynamic checks will be skipped")

class RepositoryEvaluator:
    def __init__(self, db_path=None, openai_api_key=None):
        self.db = DatabaseManager(db_path or 'evaluation.db')
        if openai_api_key and openai:
            openai.api_key = openai_api_key
        self.openai_available = bool(openai_api_key and openai)
        self.playwright_available = bool(sync_playwright)
    
    def clone_repository(self, repo_url, commit_sha, temp_dir):
        """Clone repository and checkout specific commit"""
        try:
            # Clone the repository
            subprocess.run([
                'git', 'clone', repo_url, temp_dir
            ], check=True, capture_output=True)
            
            # Checkout specific commit
            subprocess.run([
                'git', 'checkout', commit_sha
            ], cwd=temp_dir, check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            return False
    
    def check_mit_license(self, repo_path):
        """Check if repository has MIT license"""
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'license', 'license.txt']
        
        for license_file in license_files:
            license_path = Path(repo_path) / license_file
            if license_path.exists():
                try:
                    content = license_path.read_text(encoding='utf-8').lower()
                    if 'mit license' in content or 'mit' in content:
                        return True, "MIT license found"
                except Exception as e:
                    print(f"Error reading license file: {e}")
        
        return False, "MIT license not found"
    
    def check_readme_quality(self, repo_path):
        """Check README.md quality using LLM"""
        readme_path = Path(repo_path) / 'README.md'
        
        if not readme_path.exists():
            return 0.0, "README.md not found"
        
        try:
            readme_content = readme_path.read_text(encoding='utf-8')
        except Exception as e:
            return 0.0, f"Error reading README.md: {e}"
        
        if not self.openai_available:
            # Fallback scoring based on basic criteria
            score = 0.0
            criteria_met = []
            
            if len(readme_content) > 500:
                score += 0.2
                criteria_met.append("adequate length")
            
            if '# ' in readme_content:
                score += 0.2
                criteria_met.append("has headings")
            
            if any(section in readme_content.lower() for section in ['setup', 'installation', 'usage']):
                score += 0.2
                criteria_met.append("has setup/usage sections")
            
            if any(section in readme_content.lower() for section in ['license', 'mit']):
                score += 0.2
                criteria_met.append("mentions license")
            
            if '```' in readme_content:
                score += 0.2
                criteria_met.append("has code examples")
            
            return min(score, 1.0), f"Basic criteria met: {', '.join(criteria_met)}"
        
        try:
            prompt = f"""
            Evaluate the quality of this README.md file on a scale of 0.0 to 1.0:

            {readme_content[:2000]}...

            Consider:
            - Professional presentation
            - Clear structure and organization
            - Comprehensive setup instructions
            - Usage examples
            - Code explanation
            - License information

            Respond with just a number between 0.0 and 1.0, followed by a brief explanation.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            lines = result.split('\n')
            score_line = lines[0]
            
            try:
                score = float(score_line.split()[0])
                explanation = ' '.join(lines[1:]) if len(lines) > 1 else "LLM evaluation"
                return min(max(score, 0.0), 1.0), explanation
            except (ValueError, IndexError):
                return 0.5, f"LLM response parsing error: {result}"
                
        except Exception as e:
            return 0.5, f"LLM evaluation error: {e}"
    
    def check_code_quality(self, repo_path):
        """Check code quality using LLM"""
        if not self.openai_available:
            return 0.5, "LLM not available for code quality check"
        
        # Find code files
        code_files = []
        for ext in ['.html', '.css', '.js', '.py', '.java', '.cpp', '.c']:
            code_files.extend(Path(repo_path).glob(f'**/*{ext}'))
        
        if not code_files:
            return 0.0, "No code files found"
        
        # Read up to 3 main code files
        code_content = ""
        files_read = 0
        
        for file_path in code_files[:3]:
            try:
                content = file_path.read_text(encoding='utf-8')
                code_content += f"\n\n=== {file_path.name} ===\n{content[:1000]}"
                files_read += 1
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        if not code_content:
            return 0.0, "No readable code files"
        
        try:
            prompt = f"""
            Evaluate the quality of this code on a scale of 0.0 to 1.0:

            {code_content[:3000]}...

            Consider:
            - Code organization and structure
            - Comments and documentation
            - Error handling
            - Best practices
            - Functionality implementation

            Respond with just a number between 0.0 and 1.0, followed by a brief explanation.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            lines = result.split('\n')
            score_line = lines[0]
            
            try:
                score = float(score_line.split()[0])
                explanation = ' '.join(lines[1:]) if len(lines) > 1 else "LLM code evaluation"
                return min(max(score, 0.0), 1.0), explanation
            except (ValueError, IndexError):
                return 0.5, f"LLM response parsing error: {result}"
                
        except Exception as e:
            return 0.5, f"LLM code evaluation error: {e}"
    
    def check_pages_accessibility(self, pages_url):
        """Check if GitHub Pages is accessible"""
        try:
            response = requests.get(pages_url, timeout=10)
            if response.status_code == 200:
                return True, f"Pages accessible (HTTP {response.status_code})"
            else:
                return False, f"Pages not accessible (HTTP {response.status_code})"
        except Exception as e:
            return False, f"Pages accessibility error: {e}"
    
    def dynamic_check_playwright(self, pages_url, task_data):
        """Run dynamic checks using Playwright"""
        if not self.playwright_available:
            return 0.5, "Playwright not available for dynamic checks"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # Navigate to the page
                page.goto(pages_url, timeout=30000)
                
                # Wait for page to load
                page.wait_for_load_state('networkidle')
                
                score = 0.0
                checks_passed = []
                
                # Check if page loads without errors
                title = page.title()
                if title and title.strip():
                    score += 0.3
                    checks_passed.append("page has title")
                
                # Check if page has content
                body_text = page.inner_text('body')
                if len(body_text.strip()) > 50:
                    score += 0.3
                    checks_passed.append("page has content")
                
                # Check for task-specific functionality
                task_type = task_data.get('task', '').split('-')[0]
                
                if task_type == 'captcha':
                    # Look for URL parameter handling
                    test_url = f"{pages_url}?url=test"
                    page.goto(test_url)
                    
                    # Check if URL parameter is processed
                    if 'test' in page.inner_text('body').lower():
                        score += 0.4
                        checks_passed.append("URL parameter handling")
                
                elif task_type == 'weather':
                    # Look for city parameter handling
                    test_url = f"{pages_url}?city=London"
                    page.goto(test_url)
                    
                    # Check if city parameter is processed
                    if 'london' in page.inner_text('body').lower():
                        score += 0.4
                        checks_passed.append("city parameter handling")
                
                elif task_type == 'todo':
                    # Look for todo functionality
                    try:
                        # Try to find input fields or buttons
                        inputs = page.query_selector_all('input')
                        buttons = page.query_selector_all('button')
                        
                        if inputs and buttons:
                            score += 0.4
                            checks_passed.append("todo interface elements")
                    except:
                        pass
                
                browser.close()
                
                return min(score, 1.0), f"Dynamic checks passed: {', '.join(checks_passed)}"
                
        except Exception as e:
            return 0.0, f"Dynamic check error: {e}"
    
    def evaluate_repository(self, repo_data):
        """Evaluate a single repository"""
        email = repo_data['email']
        task = repo_data['task']
        round_num = repo_data['round']
        repo_url = repo_data['repo_url']
        commit_sha = repo_data['commit_sha']
        pages_url = repo_data['pages_url']
        
        print(f"\nEvaluating {email} - {task} (Round {round_num})")
        
        results = []
        
        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            clone_success = self.clone_repository(repo_url, commit_sha, temp_dir)
            
            if clone_success:
                # Check MIT license
                has_license, license_reason = self.check_mit_license(temp_dir)
                results.append({
                    'email': email,
                    'task': task,
                    'round': round_num,
                    'repo_url': repo_url,
                    'commit_sha': commit_sha,
                    'pages_url': pages_url,
                    'check_name': 'MIT License',
                    'score': 1.0 if has_license else 0.0,
                    'reason': license_reason,
                    'logs': ''
                })
                
                # Check README quality
                readme_score, readme_reason = self.check_readme_quality(temp_dir)
                results.append({
                    'email': email,
                    'task': task,
                    'round': round_num,
                    'repo_url': repo_url,
                    'commit_sha': commit_sha,
                    'pages_url': pages_url,
                    'check_name': 'README Quality',
                    'score': readme_score,
                    'reason': readme_reason,
                    'logs': ''
                })
                
                # Check code quality
                code_score, code_reason = self.check_code_quality(temp_dir)
                results.append({
                    'email': email,
                    'task': task,
                    'round': round_num,
                    'repo_url': repo_url,
                    'commit_sha': commit_sha,
                    'pages_url': pages_url,
                    'check_name': 'Code Quality',
                    'score': code_score,
                    'reason': code_reason,
                    'logs': ''
                })
            else:
                # Repository clone failed
                results.append({
                    'email': email,
                    'task': task,
                    'round': round_num,
                    'repo_url': repo_url,
                    'commit_sha': commit_sha,
                    'pages_url': pages_url,
                    'check_name': 'Repository Access',
                    'score': 0.0,
                    'reason': 'Failed to clone repository',
                    'logs': ''
                })
        
        # Check GitHub Pages accessibility
        pages_accessible, pages_reason = self.check_pages_accessibility(pages_url)
        results.append({
            'email': email,
            'task': task,
            'round': round_num,
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url,
            'check_name': 'Pages Accessibility',
            'score': 1.0 if pages_accessible else 0.0,
            'reason': pages_reason,
            'logs': ''
        })
        
        # Dynamic checks with Playwright
        if pages_accessible:
            dynamic_score, dynamic_reason = self.dynamic_check_playwright(pages_url, repo_data)
            results.append({
                'email': email,
                'task': task,
                'round': round_num,
                'repo_url': repo_url,
                'commit_sha': commit_sha,
                'pages_url': pages_url,
                'check_name': 'Dynamic Functionality',
                'score': dynamic_score,
                'reason': dynamic_reason,
                'logs': ''
            })
        
        # Store results in database
        for result in results:
            self.db.insert_result(result)
        
        return results
    
    def evaluate_all_repositories(self):
        """Evaluate all repositories in the database"""
        repos = self.db.get_repos()
        
        if not repos:
            print("No repositories found for evaluation")
            return
        
        print(f"Found {len(repos)} repositories to evaluate")
        
        for repo in repos:
            try:
                self.evaluate_repository(repo)
                time.sleep(2)  # Brief delay between evaluations
            except Exception as e:
                print(f"Error evaluating repository for {repo['email']}: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate submitted repositories')
    parser.add_argument('--db-path', 
                       help='Path to database file (default: evaluation.db)')
    parser.add_argument('--openai-key',
                       help='OpenAI API key for LLM evaluations')
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = RepositoryEvaluator(args.db_path, args.openai_key)
    
    print("=== Repository Evaluator ===")
    print(f"Database: {args.db_path or 'evaluation.db'}")
    print(f"OpenAI available: {evaluator.openai_available}")
    print(f"Playwright available: {evaluator.playwright_available}")
    print()
    
    # Evaluate all repositories
    evaluator.evaluate_all_repositories()
    
    print("\n=== Evaluation Complete ===")

if __name__ == "__main__":
    main()