import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/discounts")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "your-secret-key")
    API_DEBUG: bool = os.getenv("API_DEBUG", "True").lower() == "true"

settings = Settings()
