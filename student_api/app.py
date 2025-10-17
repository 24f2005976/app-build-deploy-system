from flask import Flask, request, jsonify
import json
import os
import base64
import time
import hashlib
import uuid
from datetime import datetime
import requests
from github import Github
import tempfile
import shutil
from pathlib import Path
import openai

app = Flask(__name__)

# Configuration - these should be set via environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
STUDENT_SECRET = os.getenv('STUDENT_SECRET')  # Student's secret from the form

# Initialize clients
github_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
openai.api_key = OPENAI_API_KEY

class AppGenerator:
    def __init__(self):
        pass
    
    def generate_app(self, brief, attachments=None):
        """Generate app code based on brief and attachments using LLM"""
        try:
            # Create prompt for LLM
            prompt = f"""
            Generate a complete HTML/CSS/JavaScript web application based on this brief:
            {brief}
            
            Requirements:
            - Create a single HTML file with embedded CSS and JavaScript
            - Make it professional and functional
            - Include proper error handling
            - Make it responsive
            - Add appropriate comments
            
            Return the complete HTML code.
            """
            
            if OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )
                return response.choices[0].message.content
            else:
                # Fallback for demo purposes
                return self._generate_fallback_app(brief)
        except Exception as e:
            print(f"Error generating app: {e}")
            return self._generate_fallback_app(brief)
    
    def _generate_fallback_app(self, brief):
        """Fallback app generator when LLM is not available"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated App</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .brief {{
            background: #e9f7ef;
            padding: 15px;
            border-left: 4px solid #27ae60;
            margin: 20px 0;
        }}
        .status {{
            padding: 10px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Auto-Generated Application</h1>
        <div class="brief">
            <h3>Project Brief:</h3>
            <p>{brief}</p>
        </div>
        <div class="status">
            <strong>Status:</strong> Application generated successfully!
        </div>
        <div id="app-content">
            <h3>Application Features:</h3>
            <ul>
                <li>Responsive design</li>
                <li>Professional layout</li>
                <li>Based on provided brief</li>
                <li>Ready for deployment</li>
            </ul>
        </div>
    </div>
    <script>
        console.log('App loaded successfully');
        // Add your application logic here
    </script>
</body>
</html>"""

class GitHubManager:
    def __init__(self, token):
        self.github = Github(token)
        self.user = self.github.get_user()
    
    def create_repo(self, repo_name, description="Auto-generated application"):
        """Create a new public repository"""
        try:
            repo = self.user.create_repo(
                name=repo_name,
                description=description,
                private=False,
                auto_init=False
            )
            return repo
        except Exception as e:
            print(f"Error creating repo: {e}")
            raise
    
    def upload_files(self, repo, files):
        """Upload files to repository"""
        try:
            for file_path, content in files.items():
                repo.create_file(
                    path=file_path,
                    message=f"Add {file_path}",
                    content=content
                )
        except Exception as e:
            print(f"Error uploading files: {e}")
            raise
    
    def enable_pages(self, repo):
        """Enable GitHub Pages for the repository"""
        try:
            # GitHub Pages API endpoint
            url = f"https://api.github.com/repos/{repo.full_name}/pages"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "source": {
                    "branch": "main",
                    "path": "/"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code in [201, 409]:  # 409 if already enabled
                return True
            else:
                print(f"Error enabling pages: {response.text}")
                return False
        except Exception as e:
            print(f"Error enabling GitHub Pages: {e}")
            return False

def verify_secret(provided_secret):
    """Verify the student's secret"""
    return provided_secret == STUDENT_SECRET

def generate_mit_license():
    """Generate MIT LICENSE content"""
    year = datetime.now().year
    return f"""MIT License

Copyright (c) {year} Student

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

def generate_readme(task, brief, repo_url):
    """Generate professional README.md"""
    return f"""# {task.replace('-', ' ').title()}

## Summary

This application was automatically generated based on the following brief:

> {brief}

## Setup

1. Clone the repository:
   ```bash
   git clone {repo_url}
   cd {repo_url.split('/')[-1]}
   ```

2. Open `index.html` in your web browser or serve it using a simple HTTP server:
   ```bash
   python -m http.server 8000
   ```

## Usage

Open the application in your web browser. The application is designed to be intuitive and user-friendly.

## Code Explanation

This application consists of:

- **HTML Structure**: Semantic HTML5 markup for accessibility and SEO
- **CSS Styling**: Responsive design that works on all devices
- **JavaScript Logic**: Interactive functionality as specified in the brief

### Key Features

- Responsive design
- Professional styling
- Error handling
- Cross-browser compatibility

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Deployment

This application is automatically deployed to GitHub Pages and accessible at:
{repo_url.replace('github.com', 'github.io').replace('/', '/', 1)}

---

*This application was generated automatically as part of the IITM application development project.*
"""

def notify_evaluation_api(data, max_retries=5):
    """Notify evaluation API with exponential backoff"""
    evaluation_url = data.get('evaluation_url')
    if not evaluation_url:
        return False
    
    payload = {
        'email': data['email'],
        'task': data['task'],
        'round': data['round'],
        'nonce': data['nonce'],
        'repo_url': data['repo_url'],
        'commit_sha': data['commit_sha'],
        'pages_url': data['pages_url']
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                evaluation_url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"Successfully notified evaluation API")
                return True
            else:
                print(f"Evaluation API returned {response.status_code}: {response.text}")
        
        except Exception as e:
            print(f"Error notifying evaluation API (attempt {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            delay = 2 ** attempt  # Exponential backoff: 1, 2, 4, 8, 16 seconds
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    return False

@app.route('/api/build', methods=['POST'])
def build_application():
    """Main endpoint for building and deploying applications"""
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'secret', 'task', 'round', 'nonce', 'brief', 'evaluation_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify secret
        if not verify_secret(data['secret']):
            return jsonify({'error': 'Invalid secret'}), 401
        
        # Check if GitHub client is available
        if not github_client:
            return jsonify({'error': 'GitHub integration not configured'}), 500
        
        # Generate unique repo name
        repo_name = f"{data['task']}-{hashlib.md5(data['email'].encode()).hexdigest()[:8]}"
        
        # Initialize components
        app_generator = AppGenerator()
        github_manager = GitHubManager(GITHUB_TOKEN)
        
        # Generate application code
        print(f"Generating application for: {data['brief']}")
        app_code = app_generator.generate_app(data['brief'], data.get('attachments'))
        
        # Create repository
        print(f"Creating repository: {repo_name}")
        repo = github_manager.create_repo(repo_name, f"Auto-generated app: {data['task']}")
        
        # Prepare files
        files = {
            'index.html': app_code,
            'LICENSE': generate_mit_license(),
            'README.md': generate_readme(data['task'], data['brief'], repo.html_url)
        }
        
        # Process attachments if any
        if data.get('attachments'):
            for attachment in data['attachments']:
                if attachment.get('url') and attachment['url'].startswith('data:'):
                    # Decode data URI
                    header, encoded = attachment['url'].split(',', 1)
                    file_data = base64.b64decode(encoded)
                    files[attachment['name']] = file_data.decode('utf-8', errors='ignore')
        
        # Upload files to repository
        print("Uploading files to repository")
        github_manager.upload_files(repo, files)
        
        # Enable GitHub Pages
        print("Enabling GitHub Pages")
        pages_enabled = github_manager.enable_pages(repo)
        
        # Get commit SHA
        commits = list(repo.get_commits())
        commit_sha = commits[0].sha if commits else "unknown"
        
        # Generate Pages URL
        pages_url = f"https://{github_client.get_user().login}.github.io/{repo_name}/"
        
        # Prepare notification data
        notification_data = {
            'email': data['email'],
            'task': data['task'],
            'round': data['round'],
            'nonce': data['nonce'],
            'repo_url': repo.html_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url,
            'evaluation_url': data['evaluation_url']
        }
        
        # Notify evaluation API
        print("Notifying evaluation API")
        notification_success = notify_evaluation_api(notification_data)
        
        # Return success response
        response = {
            'status': 'success',
            'message': 'Application built and deployed successfully',
            'repo_url': repo.html_url,
            'pages_url': pages_url,
            'commit_sha': commit_sha,
            'pages_enabled': pages_enabled,
            'evaluation_notified': notification_success
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error in build_application: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'github_configured': GITHUB_TOKEN is not None,
        'openai_configured': OPENAI_API_KEY is not None
    }), 200

if __name__ == '__main__':
    # Check environment variables
    if not GITHUB_TOKEN:
        print("WARNING: GITHUB_TOKEN not set. GitHub integration will not work.")
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY not set. Using fallback app generator.")
    if not STUDENT_SECRET:
        print("WARNING: STUDENT_SECRET not set. Secret verification will fail.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)