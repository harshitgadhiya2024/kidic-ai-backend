"""Application settings and configuration"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    app_name: str = Field(default="Kidic AI", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8020, alias="PORT")
    
    # MongoDB Configuration
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="kidic_ai", alias="MONGODB_DB_NAME")
    
    # JWT Configuration
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # OTP Configuration
    otp_expire_minutes: int = Field(default=10, alias="OTP_EXPIRE_MINUTES")
    otp_length: int = Field(default=6, alias="OTP_LENGTH")
    
    # SMTP Configuration for Email
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(..., alias="SMTP_USERNAME")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    smtp_sender_email: str = Field(..., alias="SMTP_SENDER_EMAIL")
    smtp_sender_name: str = Field(default="Kidic AI", alias="SMTP_SENDER_NAME")
    
    # AWS SES Configuration (optional - keeping for S3)
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    
    # AWS S3 Configuration
    aws_s3_bucket_name: str = Field(..., alias="AWS_S3_BUCKET_NAME")
    aws_s3_region: str = Field(default="us-east-1", alias="AWS_S3_REGION")
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000", 
        alias="CORS_ORIGINS"
    )
    
    # User Settings
    default_user_credits: int = Field(default=1, alias="DEFAULT_USER_CREDITS")

    # AI Image Generation API Configuration
    # Seeddream API (Primary)
    seeddream_api_key: str = Field(..., alias="SEEDDREAM_API_KEY")
    seeddream_create_task_url: str = Field(
        default="https://api.kie.ai/api/v1/jobs/createTask",
        alias="SEEDDREAM_CREATE_TASK_URL"
    )
    seeddream_get_task_url: str = Field(
        default="https://api.kie.ai/api/v1/jobs/recordInfo",
        alias="SEEDDREAM_GET_TASK_URL"
    )
    seeddream_model: str = Field(
        default="seedream/4.5-edit",
        alias="SEEDDREAM_MODEL"
    )
    seeddream_quality: str = Field(
        default="high",
        alias="SEEDDREAM_QUALITY"
    )

    # Gemini API (Fallback)
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    gemini_model: str = Field(
        default="gemini-3-pro-image-preview",
        alias="GEMINI_MODEL"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
