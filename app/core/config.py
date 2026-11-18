from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
# Load this project's settings before reading environment variables. Existing
# process-level variables remain authoritative (python-dotenv's default).
load_dotenv(BASE_DIR / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'precast_estimator.db'}")

# The local Ollama defaults retain an offline setup. Set VISION_PROVIDER to
# "openai_compatible" for a hosted or self-hosted compatible chat endpoint.
_legacy_ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "ollama").lower()
VISION_API_URL = os.getenv("VISION_API_URL", _legacy_ollama_url)
VISION_API_KEY = os.getenv("VISION_API_KEY")
VISION_MODEL = os.getenv("VISION_MODEL", os.getenv("OLLAMA_VISION_MODEL", ""))


def _csv_setting(name: str, default: str = "") -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


ALLOWED_ORIGINS = _csv_setting("ALLOWED_ORIGINS")
ALLOWED_HOSTS = _csv_setting("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
