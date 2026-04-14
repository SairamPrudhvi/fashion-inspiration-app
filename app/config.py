import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent  # project root

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Build an absolute database path so it doesn't depend on cwd
_db_path = BASE_DIR / "data" / "fashion.db"
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")

UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads")))

# Make sure these directories exist at import time
(BASE_DIR / "data").mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
