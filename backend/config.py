import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
    OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1-hd")
    OPENAI_STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
    
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    SECRET_KEY = os.getenv("SECRET_KEY", "sekta-gold-change-me-in-prod")
    
    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
    ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
    ENABLE_IMAGE_GEN = os.getenv("ENABLE_IMAGE_GEN", "true").lower() == "true"
    ENABLE_VOICE = os.getenv("ENABLE_VOICE", "true").lower() == "true"
    ENABLE_CODE_INTERPRETER = os.getenv("ENABLE_CODE_INTERPRETER", "true").lower() == "true"
    
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Validate
    @classmethod
    def check(cls):
        if not cls.OPENAI_API_KEY or "YOUR_NEW_KEY" in cls.OPENAI_API_KEY:
            print("⚠️  WARNING: OPENAI_API_KEY not set! Set it in .env file")
            print("   Copy .env.example to .env and add your new key")
            print("   If you pasted key in chat, REVOKE it at platform.openai.com/api-keys")
            return False
        if cls.OPENAI_API_KEY.startswith("sk-proj-4R35"):
            print("🚨 CRITICAL: You are using the COMPROMISED leaked key!")
            print("   This key was exposed in chat. Revoke it NOW at https://platform.openai.com/api-keys")
            print("   Create a new one!")
            return False
        return True

config = Config()
