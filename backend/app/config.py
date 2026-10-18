"""Centralized configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    use_vertexai: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    gemini_flash_model: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
    gemini_pro_model: str = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")

    simulator_interval_seconds: float = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "8"))

    allowed_origins: list[str] = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()
    ]


settings = Settings()

