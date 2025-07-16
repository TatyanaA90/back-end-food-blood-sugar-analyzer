from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()