from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str

    api_key: str = "change-me"
    webhook_token: str | None = None

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()

