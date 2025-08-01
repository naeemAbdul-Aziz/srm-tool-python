# config.py
# Configuration settings and environment variables
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration - use environment variables for security
DB_NAME = os.getenv("DB_NAME", "srms-db")
DB_USER = os.getenv("DB_USER", "postgres") 
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # Must be set in .env file
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Application configuration
APP_DEBUG = os.getenv("APP_DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "")  # Must be set in .env file for production
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour default

# Validate critical configuration
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable must be set")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")
