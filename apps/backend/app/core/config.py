from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tribi Backend"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "tribi"
    MYSQL_PASSWORD: str = "tribi"
    MYSQL_DB: str = "tribi"
    BACKEND_PORT: int = 8000
    # Auth / Email / Payments
    JWT_SECRET: str = "dev-secret"
    JWT_EXPIRES_MIN: int = 60
    EMAIL_FROM: str = "dev@tribi.local"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    PAYMENT_PROVIDER: str = "MOCK"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
