import os
import sys
from pathlib import Path
import streamlit as st

class Config:
    # Get API key from secrets or use embedded
    try:
        OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
    except:
        OPENROUTER_API_KEY = "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"
    
    # Model Configuration
    MODEL_NAME = 'meta-llama/llama-3.3-70b-instruct:free'
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        APPLICATION_PATH = Path(sys.executable).parent
    else:
        APPLICATION_PATH = Path(__file__).parent
    
    # Data folder in same directory
    DATA_FOLDER = str(APPLICATION_PATH / 'data')
    CSV_CACHE_FOLDER = str(APPLICATION_PATH / 'data' / 'csv_cache')
    
    # Log file for admin debugging
    LOG_FILE = str(APPLICATION_PATH / 'app_debug.log')
    LAST_SCAN_FILE = str(APPLICATION_PATH / '.last_scan')
    
    @classmethod
    def validate(cls):
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API Key not configured")
        
        # Create data folder if it doesn't exist
        if not os.path.exists(cls.DATA_FOLDER):
            os.makedirs(cls.DATA_FOLDER)
        
        # Create cache folder
        os.makedirs(cls.CSV_CACHE_FOLDER, exist_ok=True)
        
        return True
    
    @classmethod
    def get_app_version(cls):
        return "1.0.0"
    
    @classmethod
    def get_data_folder(cls):
        return cls.DATA_FOLDER

try:
    Config.validate()
except Exception as e:
    print(f"Configuration Error: {e}")