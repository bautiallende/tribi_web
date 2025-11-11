from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tribi Backend"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    DATABASE_URL: str
    MYSQL_ROOT_PASSWORD: str
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_PORT: int = 3306
    BACKEND_PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
