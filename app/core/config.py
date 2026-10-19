from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
# Load this project's settings before reading environment variables. Existing
# process-level variables remain authoritative (python-dotenv's default).
load_dotenv(BASE_DIR / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'precast_estimator.db'}")

# Ollama keeps inference on the machine running this application.  A vision-capable
# model (for example qwen2.5vl) must be pulled separately by the operator.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5-coder:7b")
