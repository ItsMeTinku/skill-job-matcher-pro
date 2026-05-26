"""utils/__init__.py — utility helpers."""

import os
import uuid
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename: str) -> bool:
    """Return True if *filename* has a permitted extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_uploaded_file(file_obj, upload_folder: str) -> tuple[str, str]:
    """
    Sanitise filename, prepend a UUID, save to *upload_folder*.

    Returns
    -------
    (stored_filename, original_filename)
    """
    original  = secure_filename(file_obj.filename)
    ext       = original.rsplit(".", 1)[1].lower()
    stored    = f"{uuid.uuid4().hex}.{ext}"
    filepath  = os.path.join(upload_folder, stored)
    file_obj.save(filepath)
    return stored, original
