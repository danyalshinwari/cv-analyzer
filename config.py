import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Configuration settings
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# Default models
GEMINI_MODEL = "gemini-1.5-flash"

# Application settings
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)