#!/usr/bin/env python3
"""
Test script for the App Build Deploy System
"""

import json
import requests
import time
import sys
from datetime import datetime

def test_student_api():
    """Test the student API endpoint"""
    print("Testing Student API...")
    
    # Health check
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Student API health check passed")
            health_data = response.json()
            print(f"   GitHub configured: {health_data.get('github_configured', False)}")
            print(f"   OpenAI configured: {health_data.get('openai_configured', False)}")
        else:
            print("❌ Student API health check failed")
            return False
    except Exception as e:
        print(f"❌ Student API not accessible: {e}")
        return False
    
    return True

def test_evaluation_api():
    """Test the evaluation API endpoint"""
    print("Testing Evaluation API...")
    
    # Health check
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Evaluation API health check passed")
        else:
            print("❌ Evaluation API health check failed")
            return False
    except Exception as e:
        print(f"❌ Evaluation API not accessible: {e}")
        return False
    
    return True

def test_database():
    """Test database operations"""
    print("Testing Database...")
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))
        from database import DatabaseManager
        
        db = DatabaseManager('test_evaluation.db')
        print("✅ Database connection successful")
        
        # Test submission insertion
        test_submission = {
            'email': 'test@example.com',
            'endpoint': 'http://localhost:5000/api/build',
            'secret': 'test_secret'
        }
        
        success = db.insert_submission(test_submission)
        if success:
            print("✅ Database submission insertion successful")
        else:
            print("❌ Database submission insertion failed")
            return False
        
        # Clean up test database
        import os
        if os.path.exists('test_evaluation.db'):
            os.remove('test_evaluation.db')
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_security_validation():
    """Test security validation functions"""
    print("Testing Security Validation...")
    
    try:
        from security import SecurityValidator
        
        # Test email validation
        valid_email = SecurityValidator.validate_email('test@example.com')
        invalid_email = SecurityValidator.validate_email('invalid-email')
        
        if valid_email and not invalid_email:
            print("✅ Email validation working")
        else:
            print("❌ Email validation failed")
            return False
        
        # Test URL validation
        valid_url = SecurityValidator.validate_url('https://example.com/path')
        invalid_url = SecurityValidator.validate_url('not-a-url')
        
        if valid_url and not invalid_url:
            print("✅ URL validation working")
        else:
            print("❌ URL validation failed")
            return False
        
        # Test secret scanning
        test_content = "api_key = 'sk-1234567890abcdef1234567890abcdef12345678'"
        secrets = SecurityValidator.scan_for_secrets(test_content)
        
        if secrets:
            print("✅ Secret scanning working")
        else:
            print("❌ Secret scanning failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Security validation test failed: {e}")
        return False

def test_task_templates():
    """Test task template system"""
    print("Testing Task Templates...")
    
    try:
        from evaluation_system.round1 import TaskTemplates
        
        templates = TaskTemplates.get_templates()
        
        if templates and 'captcha-solver' in templates:
            print("✅ Task templates loaded successfully")
            
            # Check template structure
            captcha_template = templates['captcha-solver']
            if 'round1' in captcha_template and 'round2' in captcha_template:
                print("✅ Template structure valid")
            else:
                print("❌ Template structure invalid")
                return False
        else:
            print("❌ Task templates not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Task template test failed: {e}")
        return False

def test_full_workflow():
    """Test a simulated full workflow"""
    print("Testing Full Workflow Simulation...")
    
    # This would test the complete flow but requires actual GitHub token
    # For now, just validate the request structure
    
    test_request = {
        "email": "test@example.com",
        "secret": "test_secret",
        "task": "captcha-solver-abc123",
        "round": 1,
        "nonce": "12345678-1234-1234-1234-123456789012",
        "brief": "Create a captcha solver that handles image URLs",
        "checks": [
            "Repo has MIT license",
            "README.md is professional",
            "Page displays captcha URL",
            "Page displays solved text"
        ],
        "evaluation_url": "http://localhost:5001/api/notify",
        "attachments": []
    }
    
    try:
        from security import SecurityValidator
        
        is_valid, message = SecurityValidator.validate_task_data(test_request)
        
        if is_valid:
            print("✅ Request validation successful")
            return True
        else:
            print(f"❌ Request validation failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("App Build Deploy System - Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Student API", test_student_api),
        ("Evaluation API", test_evaluation_api),
        ("Database", test_database),
        ("Security Validation", test_security_validation),
        ("Task Templates", test_task_templates),
        ("Full Workflow", test_full_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name} Test:")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)