import os
from utils.logger import Logger
from dotenv import load_dotenv

class SocialsManager:
    """Manager class for handling social media posts."""
    
    def __init__(self, model=None):
        """Initialize the socials manager."""
        self.logger = Logger(model=model)
        self.model = model
        load_dotenv()
        
        # Add debug logging for initialization
        self.logger.debug(f"🔧 SocialsManager initialized")
