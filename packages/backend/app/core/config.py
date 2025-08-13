from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
import secrets


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PMO Agent"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "pmo_agent"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
        )
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = "PMO Agent"
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    
    # OpenAI API
    USE_OPENAI: bool = True
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-5-mini"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_VERBOSITY: str = "low"
    OPENAI_REASONING_EFFORT: str = "low"
    
    # AWS Bedrock
    USE_BEDROCK: bool = False
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = None
    
    @validator("ENCRYPTION_KEY", pre=True)
    def generate_encryption_key(cls, v: Optional[str]) -> str:
        if v:
            return v
        # Generate a new key if not provided
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Testing
    TESTING: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()