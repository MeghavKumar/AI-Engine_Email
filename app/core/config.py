from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Email Engine"
    app_env: str = "development"

    database_url: str = (
        "postgresql+psycopg://"
        "email_engine:email_engine@postgres:5432/email_engine"
    )

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    follow_up_days: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
