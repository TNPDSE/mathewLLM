import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    """
    Application configuration settings.
    """

    ENDPOINT: str = os.getenv("ENDPOINT")
    API_KEY: str = os.getenv("API_KEY")
    DEPLOYMENT_NAME: str = os.getenv("DEPLOYMENT_NAME")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY")
    AUDIT_FILE: str = os.getenv("AUDIT_FILE")
    AUDIT_FILE = Path.cwd() / "app" / "audit_qa_with_category_desc.json"
    API_URL = os.getenv("API_URL")
    RESET_URL = os.getenv("RESET_URL")

settings = Settings()

def validate_settings():
    if not settings.ENDPOINT:
        raise ValueError("Endpoint not set in environment")
    if not settings.API_KEY:
        raise ValueError("API key not set in environment")
    if not settings.DEPLOYMENT_NAME:
        raise ValueError("Deployment name not set in environment")
    if not settings.INTERNAL_API_KEY:
        raise ValueError("Internal API key not set in environment")
    if not settings.AUDIT_FILE or not settings.AUDIT_FILE.exists():
        raise ValueError("Audit file not set or does not exist in environment")
