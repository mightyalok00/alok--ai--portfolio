from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    site_name: str = "Alok Agarwal | Search, Data & AI"
    owner_name: str = "Alok Agarwal"
    tagline: str = "SEO, marketing analytics, data science and applied AI projects"
    bio: str = "SEO strategist and digital marketer building deeper expertise in analytics, data science and AI/ML."
    location: str = "Jodhpur, India"
    contact_email: str = "classyalok00@gmail.com"
    contact_phone: str = "8209709106"
    github_url: str = "https://github.com/mightyalok00"
    linkedin_url: str = "https://www.linkedin.com/in/alok-agarwal-seo-digital-marketing/"
    instagram_url: str = ""
    site_url: str = "http://127.0.0.1:8000"
    admin_password: str = "change-this-before-deploying"
    session_secret: str = "development-only-change-this-secret"
    database_url: str = "sqlite:///./portfolio.db"
    app_env: str = "development"
    https_only: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
