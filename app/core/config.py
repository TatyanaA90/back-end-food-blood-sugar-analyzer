from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str
    FRONTEND_URL: str = "http://localhost:5173"
    
    # JWT Settings
    SECRET_KEY: str = "your-secret-key"  # Should be overridden in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SMTP Settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025  # Default port for mailhog
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = False
    SMTP_SENDER: str = "noreply@example.com"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()