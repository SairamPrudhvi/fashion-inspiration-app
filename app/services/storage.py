import shutil
import uuid
from pathlib import Path
from ..config import UPLOAD_DIR

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def save_upload(file_obj, original_filename: str) -> tuple:
    """
    Write the uploaded file to disk under a UUID-based name.
    Returns (stored_filename, absolute_path_string).
    """
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}")

    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / unique_name

    with open(dest, "wb") as out:
        shutil.copyfileobj(file_obj, out)

    return unique_name, str(dest)


def delete_file(filename: str) -> None:
    path = UPLOAD_DIR / filename
    if path.exists():
        path.unlink()


def get_abs_path(filename: str) -> str:
    return str(UPLOAD_DIR / filename)
