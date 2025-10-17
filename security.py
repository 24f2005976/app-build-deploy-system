"""
Security utilities for the app build deploy system
"""

import re
import os
import json
import hashlib
import tempfile
import subprocess
from typing import Dict, List, Tuple, Any

class SecurityValidator:
    """Security validation and sanitization utilities"""
    
    # Dangerous patterns that should not be in code
    DANGEROUS_PATTERNS = [
        r'api[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}',
        r'secret[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}',
        r'password\s*[=:]\s*["\']?[^\s"\']{8,}',
        r'token\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}',
        r'github[_-]?token\s*[=:]\s*["\']?ghp_[a-zA-Z0-9]{36}',
        r'openai[_-]?key\s*[=:]\s*["\']?sk-[a-zA-Z0-9]{48}',
    ]
    
    # Allowed file extensions for generated apps
    ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.json', '.md', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.svg'}
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    MAX_TOTAL_SIZE = 5 * 1024 * 1024  # 5MB
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/[^\s]*)?$'
        return bool(re.match(pattern, url))
    
    @classmethod
    def validate_github_repo_name(cls, name: str) -> bool:
        """Validate GitHub repository name"""
        # GitHub repo names: 1-100 chars, alphanumeric, hyphens, underscores, dots
        pattern = r'^[a-zA-Z0-9._-]{1,100}$'
        return bool(re.match(pattern, name))
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(text, str):
            return ""
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @classmethod
    def validate_task_data(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate incoming task data"""
        required_fields = ['email', 'secret', 'task', 'round', 'nonce', 'brief', 'evaluation_url']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Validate email
        if not cls.validate_email(data['email']):
            return False, "Invalid email format"
        
        # Validate URLs
        if not cls.validate_url(data['evaluation_url']):
            return False, "Invalid evaluation URL format"
        
        # Validate round
        if data['round'] not in [1, 2]:
            return False, "Round must be 1 or 2"
        
        # Validate task name
        if not re.match(r'^[a-zA-Z0-9._-]{1,50}$', data['task']):
            return False, "Invalid task name format"
        
        # Validate nonce (UUID format)
        if not re.match(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$', data['nonce']):
            return False, "Invalid nonce format"
        
        # Validate brief length
        if len(data['brief']) > 5000:
            return False, "Brief too long (max 5000 characters)"
        
        # Validate secret length
        if len(data['secret']) > 100:
            return False, "Secret too long (max 100 characters)"
        
        return True, "Valid"
    
    @classmethod
    def scan_for_secrets(cls, content: str) -> List[str]:
        """Scan content for potential secrets"""
        findings = []
        
        for pattern in cls.DANGEROUS_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append(f"Potential secret found: {match.group()[:20]}...")
        
        return findings
    
    @classmethod
    def validate_generated_files(cls, files: Dict[str, str]) -> Tuple[bool, str]:
        """Validate generated files for security issues"""
        total_size = 0
        
        for file_path, content in files.items():
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in cls.ALLOWED_EXTENSIONS:
                return False, f"Disallowed file extension: {ext}"
            
            # Check file size
            file_size = len(content.encode('utf-8'))
            if file_size > cls.MAX_FILE_SIZE:
                return False, f"File too large: {file_path} ({file_size} bytes)"
            
            total_size += file_size
            
            # Check for secrets
            secrets = cls.scan_for_secrets(content)
            if secrets:
                return False, f"Potential secrets found in {file_path}: {secrets[0]}"
        
        # Check total size
        if total_size > cls.MAX_TOTAL_SIZE:
            return False, f"Total files too large: {total_size} bytes"
        
        return True, "Files validated"
    
    @classmethod
    def sanitize_generated_code(cls, code: str) -> str:
        """Sanitize generated code to remove potential issues"""
        # Remove potential secret patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            code = re.sub(pattern, '[REDACTED]', code, flags=re.IGNORECASE)
        
        # Remove script tags with external sources
        code = re.sub(r'<script[^>]+src[^>]*>[^<]*</script>', '', code, flags=re.IGNORECASE)
        
        # Remove dangerous JavaScript functions
        dangerous_js = ['eval', 'setTimeout', 'setInterval', 'Function', 'XMLHttpRequest']
        for func in dangerous_js:
            code = re.sub(f'{func}\\s*\\(', f'// {func}(', code, flags=re.IGNORECASE)
        
        return code

class GitSecurityScanner:
    """Scan repositories for security issues"""
    
    @classmethod
    def scan_repository(cls, repo_path: str) -> Dict[str, Any]:
        """Scan repository for security issues"""
        results = {
            'secrets_found': [],
            'large_files': [],
            'suspicious_files': [],
            'total_files': 0,
            'total_size': 0
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    results['total_files'] += 1
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        results['total_size'] += file_size
                        
                        # Check for large files
                        if file_size > SecurityValidator.MAX_FILE_SIZE:
                            results['large_files'].append({
                                'path': relative_path,
                                'size': file_size
                            })
                        
                        # Check file extension
                        ext = os.path.splitext(file)[1].lower()
                        if ext not in SecurityValidator.ALLOWED_EXTENSIONS:
                            results['suspicious_files'].append({
                                'path': relative_path,
                                'reason': f'Disallowed extension: {ext}'
                            })
                            continue
                        
                        # Scan file content for secrets
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                secrets = SecurityValidator.scan_for_secrets(content)
                                if secrets:
                                    results['secrets_found'].extend([
                                        {
                                            'path': relative_path,
                                            'secret': secret
                                        } for secret in secrets
                                    ])
                        except Exception:
                            # Skip binary files or files that can't be read
                            pass
                        
                    except Exception as e:
                        results['suspicious_files'].append({
                            'path': relative_path,
                            'reason': f'Error reading file: {e}'
                        })
        
        except Exception as e:
            results['error'] = str(e)
        
        return results

class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self):
        self.requests = {}  # email -> [timestamps]
        self.max_requests_per_hour = 10
        self.max_requests_per_minute = 2
    
    def is_allowed(self, email: str) -> Tuple[bool, str]:
        """Check if request is allowed for this email"""
        import time
        current_time = time.time()
        
        if email not in self.requests:
            self.requests[email] = []
        
        # Clean old requests
        self.requests[email] = [
            req_time for req_time in self.requests[email]
            if current_time - req_time < 3600  # Keep last hour
        ]
        
        # Check minute limit
        recent_requests = [
            req_time for req_time in self.requests[email]
            if current_time - req_time < 60  # Last minute
        ]
        
        if len(recent_requests) >= self.max_requests_per_minute:
            return False, "Too many requests per minute"
        
        # Check hour limit
        if len(self.requests[email]) >= self.max_requests_per_hour:
            return False, "Too many requests per hour"
        
        # Allow request
        self.requests[email].append(current_time)
        return True, "Request allowed"

# Global rate limiter instance
rate_limiter = RateLimiter()