import os
from dotenv import load_dotenv

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
