"""
Configuration management for Personalized Outreach Architect
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    kimi_api_key: Optional[str] = Field(None, env="KIMI_API_KEY")
    kimi_base_url: str = Field(
        default="https://api.moonshot.cn/v1",
        env="KIMI_BASE_URL"
    )
    kimi_model: str = Field(
        default="moonshot-v1-128k",
        env="KIMI_MODEL"
    )

    deepseek_api_key: Optional[str] = Field(None, env="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        env="DEEPSEEK_BASE_URL"
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        env="DEEPSEEK_MODEL"
    )
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Email
    sendgrid_api_key: str = Field(..., env="SENDGRID_API_KEY")
    from_email: str = Field(..., env="FROM_EMAIL")
    from_name: str = Field(..., env="FROM_NAME")
    
    # LinkedIn
    linkedin_email: Optional[str] = Field(None, env="LINKEDIN_EMAIL")
    linkedin_password: Optional[str] = Field(None, env="LINKEDIN_PASSWORD")
    
    # External APIs
    newsapi_key: Optional[str] = Field(None, env="NEWSAPI_KEY")
    serpapi_key: Optional[str] = Field(None, env="SERPAPI_KEY")
    
    # App Settings
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_concurrent_requests: int = Field(default=5, env="MAX_CONCURRENT_REQUESTS")
    rate_limit_per_minute: int = Field(default=10, env="RATE_LIMIT_PER_MINUTE")
    
    # Agent Configuration
    min_personalization_score: float = Field(default=0.7, env="MIN_PERSONALIZATION_SCORE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    email_send_delay_seconds: int = Field(default=30, env="EMAIL_SEND_DELAY_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
