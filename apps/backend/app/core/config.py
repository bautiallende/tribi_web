from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tribi Backend"
    ENVIRONMENT: str = "development"
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
    COOKIE_SECURE: bool | None = None
    COOKIE_SAMESITE: str = "lax"

    # Observability / Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # console | json
    ENABLE_REQUEST_LOGS: bool = True
    SENTRY_DSN: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0

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
    RATE_LIMIT_CODES_PER_IP_PER_DAY: int = 25

    # Billing / Exports
    INVOICE_PREFIX: str = "TRB"
    SALES_EXPORT_FILENAME: str = "tribi-sales"

    # Payments
    PAYMENT_PROVIDER: str = "MOCK"
    DEFAULT_CURRENCY: str = "USD"
    ESIM_PROVIDER: str = "LOCAL"
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_ACCOUNT_ID: str | None = None
    STRIPE_AUTO_PAYMENT_METHODS: bool = True
    STRIPE_PAYMENT_METHOD_TYPES: list[str] | None = None

    # ConnectedYou (eSIM provider)
    CONNECTED_YOU_BASE_URL: str = "https://sandbox.api.connectedyou.com"
    CONNECTED_YOU_API_KEY: str | None = None
    CONNECTED_YOU_PARTNER_ID: str | None = None
    CONNECTED_YOU_TIMEOUT_SECONDS: int = 15
    CONNECTED_YOU_DRY_RUN: bool = True

    # Admin Access
    ADMIN_EMAILS: str = ""  # Comma-separated list of admin emails

    # Support Automation / Scheduler
    SUPPORT_SLA_HOURS_LOW: int = 72
    SUPPORT_SLA_HOURS_NORMAL: int = 24
    SUPPORT_SLA_HOURS_HIGH: int = 4
    SUPPORT_REMINDER_LEAD_MINUTES: int = 60
    SUPPORT_REMINDER_INTERVAL_MINUTES: int = 60
    SUPPORT_ESCALATION_GRACE_MINUTES: int = 30
    SUPPORT_MAX_ESCALATION_LEVEL: int = 2
    SUPPORT_DIGEST_HOUR_UTC: int = 12  # noon UTC
    JOB_LOOP_INTERVAL_SECONDS: int = 60
    JOB_ENABLED: bool = False

    # Analytics defaults
    ANALYTICS_DEFAULT_RANGE_DAYS: int = 30
    ANALYTICS_PROJECTION_WINDOW_DAYS: int = 14
    ANALYTICS_PROJECTION_HORIZON_DAYS: int = 7

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

    @property
    def cookie_secure_flag(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cookie_samesite_value(self) -> str:
        allowed = {"lax", "strict", "none"}
        value = (self.COOKIE_SAMESITE or "lax").lower()
        if value not in allowed:
            return "lax"
        return value

    @property
    def log_level_value(self) -> str:
        known = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        level = (self.LOG_LEVEL or "INFO").upper()
        return level if level in known else "INFO"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
