from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tribi Backend"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    FRONTEND_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:19006",
    ]  # Web + Expo

    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "tribi"
    MYSQL_PASSWORD: str = "tribi"
    MYSQL_DB: str = "tribi"
    BACKEND_PORT: int = 8000

    # Auth / JWT
    JWT_SECRET: str = "dev-secret"
    JWT_EXPIRES_MIN: int = 60
    COOKIE_SECRET: str = "cookie-secret-change-in-production"
    COOKIE_DOMAIN: str | None = None  # Set to .tribi.app in production

    # Email / SMTP
    EMAIL_FROM: str = "dev@tribi.local"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = False

    # Rate Limiting
    RATE_LIMIT_CODES_PER_MINUTE: int = 1
    RATE_LIMIT_CODES_PER_DAY: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_WINDOW_HOURS: int = 24

    # Payments
    PAYMENT_PROVIDER: str = "MOCK"

    # Admin Access
    ADMIN_EMAILS: str = ""  # Comma-separated list of admin emails

    @property
    def admin_emails_list(self) -> list[str]:
        """Parse admin emails from comma-separated string."""
        if not self.ADMIN_EMAILS:
            return []
        return [
            email.strip().lower()
            for email in self.ADMIN_EMAILS.split(",")
            if email.strip()
        ]

    @admin_emails_list.setter
    def admin_emails_list(self, value: list[str] | str) -> None:
        """Allow overriding admin emails list for tests."""
        if isinstance(value, list):
            self.ADMIN_EMAILS = ",".join(value)
        else:
            self.ADMIN_EMAILS = value

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
