import re

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql://corenews:changeme@postgres:5432/corenews"
    redis_url: str = "redis://redis:6379/0"
    edgar_user_agent: str | None = None
    gdelt_enabled: bool = False
    research_workspace_token_hashes: dict[str, str] = Field(default_factory=dict)
    research_signing_key: SecretStr | None = None
    research_snapshot_sources: set[str] = Field(default_factory=set)

    @field_validator("research_workspace_token_hashes")
    @classmethod
    def valid_workspace_keys(cls, values: dict[str, str]) -> dict[str, str]:
        if (
            any(not name.strip() or len(name) > 128 for name in values)
            or any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in values.values())
            or len(set(values.values())) != len(values)
        ):
            raise ValueError("Each workspace needs its own SHA-256 key digest and a name up to 128 characters.")
        return values
    
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
