import os
from dotenv import load_dotenv

# Force override to bypass Windows caching
load_dotenv(override=True)

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../data/uploads")
    VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "../../data/vector_store")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Hardcoded to bypass cache completely
    GROQ_MODEL = "llama-3.3-70b-versatile"
    
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    @classmethod
    def validate(cls):
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        return True

os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.VECTOR_STORE_DIR, exist_ok=True)