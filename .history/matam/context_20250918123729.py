"""Centralized context: loads env, creates Supabase client, and initializes Flask-Mail."""

import os
from supabase import create_client, Client
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Flask-Mail instance
mail = Mail() 