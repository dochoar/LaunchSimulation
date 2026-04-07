from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM — defaults configured for local Ollama to avoid remote API costs
    llm_api_key: str = Field(default="ollama", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="http://localhost:11434/v1", alias="LLM_BASE_URL")
    llm_model_name: str = Field(default="qwen2.5-coder:7b", alias="LLM_MODEL_NAME")

    # Boost model: same local Ollama instance
    llm_boost_api_key: str = Field(default="ollama", alias="LLM_BOOST_API_KEY")
    llm_boost_base_url: str = Field(default="http://localhost:11434/v1", alias="LLM_BOOST_BASE_URL")
    llm_boost_model_name: str = Field(default="qwen2.5-coder:7b", alias="LLM_BOOST_MODEL_NAME")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./launchsim.db", alias="DATABASE_URL"
    )

    # Vector Store
    chroma_persist_dir: str = Field(default="./chroma_db", alias="CHROMA_PERSIST_DIR")

    # App
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def effective_boost_model(self) -> str:
        return self.llm_boost_model_name

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
