"""
Enterprise configuration management using Pydantic BaseSettings.
Supports environment variables and validation.
"""

import os
from pathlib import Path
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, validator
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field, validator


def load_api_key_from_file() -> Optional[str]:
    """Load API key from text file if environment variable is not set."""
    try:
        api_key_file = Path("api_key.txt")
        if api_key_file.exists():
            return api_key_file.read_text().strip()
    except Exception:
        pass
    return None


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Holiday Destinations Generator", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.6, env="OPENAI_TEMPERATURE")
    
    # Fine-tuning configuration
    use_fine_tuned_model: bool = Field(default=True, description="Use fine-tuned model if available")
    fine_tuned_model_id: Optional[str] = Field(default="ft:gpt-3.5-turbo-0125:personal:travel-destinations-20250602:Be2LDzFz", description="Fine-tuned model ID")
    fine_tuning_epochs: int = Field(default=3, description="Number of training epochs")
    fine_tuning_learning_rate: float = Field(default=1e-5, description="Learning rate for fine-tuning")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"], 
        env="ALLOWED_HOSTS"
    )
    
    # Database
    database_url: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    
    # Caching
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    
    # API Configuration
    api_timeout: int = Field(default=30, env="API_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: int = Field(default=2, env="RETRY_DELAY")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    @validator("openai_api_key", pre=True)
    def load_api_key(cls, v):
        # If no API key provided via environment, try to load from file
        if not v or v == "":
            file_api_key = load_api_key_from_file()
            if file_api_key:
                return file_api_key
        return v
    
    @validator("openai_api_key")
    def validate_openai_api_key(cls, v):
        if not v or v == "":
            # Only validate if we're not just importing - allow empty for testing
            if os.getenv("SKIP_API_KEY_VALIDATION") != "true":
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or create api_key.txt file.")
        return v
    
    @validator("allowed_hosts", pre=True)
    def parse_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @property
    def effective_openai_model(self) -> str:
        """Get the effective OpenAI model to use (fine-tuned or base)."""
        if self.use_fine_tuned_model and self.fine_tuned_model_id:
            return self.fine_tuned_model_id
        return self.openai_model
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 