"""
Shared context for Supabase client and Flask-Mail setup.

This module provides centralized configuration and initialization for:
- Supabase client for database and storage operations
- Flask-Mail for email sending functionality
- Environment variable loading

This ensures consistent configuration across all modules in the application.
"""

import os  # For environment variable access
from supabase import create_client, Client  # Supabase client for database and storage
from flask_mail import Mail, Message  # Flask-Mail for email sending
from dotenv import load_dotenv  # For loading .env configuration

# =============================================================================
# ENVIRONMENT VARIABLE LOADING
# =============================================================================

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================

# Get Supabase configuration from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client instance for database and storage operations
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =============================================================================
# FLASK-MAIL CONFIGURATION
# =============================================================================

# Initialize Flask-Mail instance for sending emails
mail = Mail() 