import mimetypes
from pathlib import Path

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


MEGABYTE = 1024 * 1024

TYPE_BY_EXTENSION = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".webp": "image",

    ".mp4": "video",
    ".webm": "video",
    ".mov": "video",

    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".m4a": "audio",

    ".doc": "document",
    ".docx": "document",
    ".odt": "document",
    ".xls": "document",
    ".xlsx": "document",
    ".ppt": "document",
    ".pptx": "document",

    ".pdf": "pdf",

    ".txt": "other",
    ".csv": "other",
    ".zip": "other",
}

MAX_SIZE_BY_TYPE = {
    "image": 10 * MEGABYTE,
    "video": 100 * MEGABYTE,
    "audio": 30 * MEGABYTE,
    "document": 20 * MEGABYTE,
    "pdf": 20 * MEGABYTE,
    "other": 20 * MEGABYTE,
}

MIME_PREFIX_BY_TYPE = {
    "image": ("image/",),
    "video": ("video/",),
    "audio": ("audio/",),
}

DOCUMENT_MIME_TYPES = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.oasis.opendocument.text",
}

OTHER_MIME_TYPES = {
    "text/plain",
    "text/csv",
    "application/csv",
    "application/zip",
    "application/x-zip-compressed",
}


def inspect_media_upload(uploaded_file):
    normalized_name = str(uploaded_file.name).replace("\\", "/")
    original_name = Path(normalized_name).name
    extension = Path(original_name).suffix.lower()

    media_type = TYPE_BY_EXTENSION.get(extension)

    if not media_type:
        raise ValidationError("This file extension is not allowed.")

    max_size = MAX_SIZE_BY_TYPE[media_type]

    if uploaded_file.size > max_size:
        max_size_mb = max_size // MEGABYTE
        raise ValidationError(
            f"Maximum size for this file type is {max_size_mb} MB."
        )

    mime_type = (
        getattr(uploaded_file, "content_type", "")
        or mimetypes.guess_type(original_name)[0]
        or "application/octet-stream"
    ).split(";", 1)[0].lower()

    if media_type in MIME_PREFIX_BY_TYPE:
        if not mime_type.startswith(MIME_PREFIX_BY_TYPE[media_type]):
            raise ValidationError(
                "The file extension and MIME type do not match."
            )

    elif media_type == "document":
        if mime_type not in DOCUMENT_MIME_TYPES:
            raise ValidationError(
                "The document extension and MIME type do not match."
            )

    elif media_type == "pdf":
        if mime_type != "application/pdf":
            raise ValidationError(
                "The selected file is not a valid PDF upload."
            )

    elif media_type == "other":
        if mime_type not in OTHER_MIME_TYPES:
            raise ValidationError(
                "This file MIME type is not allowed."
            )

    if media_type == "image":
        try:
            uploaded_file.seek(0)

            with Image.open(uploaded_file) as image:
                image.verify()

        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError(
                "The uploaded image is invalid or damaged."
            ) from exc

        finally:
            uploaded_file.seek(0)

    return media_type, original_name, mime_type