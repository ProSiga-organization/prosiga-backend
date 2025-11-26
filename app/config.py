from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_connect_url: str
    auth_service_url: str = "http://auth-prosiga:8000/login/me"


settings = Settings()