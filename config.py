# Configuration loader for the application
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Student Configuration
    STUDENT_SECRET = os.getenv('STUDENT_SECRET')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', './database/evaluation.db')
    
    # API Configuration
    STUDENT_API_PORT = int(os.getenv('STUDENT_API_PORT', 5000))
    EVALUATION_API_PORT = int(os.getenv('EVALUATION_API_PORT', 5001))
    EVALUATION_API_URL = os.getenv('EVALUATION_API_URL', 'http://localhost:5001/api/notify')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        missing = []
        
        if not cls.GITHUB_TOKEN:
            missing.append('GITHUB_TOKEN')
        
        if not cls.STUDENT_SECRET:
            missing.append('STUDENT_SECRET')
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True