from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/als_local"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Tesseract
    tesseract_cmd: str = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    # Screenshot
    screenshot_folder: str = "hasil_screenshot_api"
    
    # Scraping
    max_attempts: int = 5
    selenium_timeout: int = 30
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Ensure screenshot folder exists
os.makedirs(settings.screenshot_folder, exist_ok=True)