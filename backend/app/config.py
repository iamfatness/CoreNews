from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql://corenews:changeme@postgres:5432/corenews"
    redis_url: str = "redis://redis:6379/0"
    
    # Free-tier API keys (loaded from .env)
    shodan_api_key: Optional[str] = None
    censys_api_token: Optional[str] = None
    virustotal_api_key: Optional[str] = None
    otx_api_key: Optional[str] = None
    abuseipdb_api_key: Optional[str] = None
    urlscan_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
