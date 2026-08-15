import wave
from pathlib import Path
from uuid import uuid4

from PIL import Image

from .models import MediaAsset
from .validators import inspect_media_upload


def _try_get_duration(uploaded_file, extension):
    if extension != ".wav":
        return None

    try:
        uploaded_file.seek(0)
        with wave.open(uploaded_file, "rb") as audio:
            frame_rate = audio.getframerate()
            if frame_rate:
                return round(audio.getnframes() / frame_rate)
    except (wave.Error, EOFError):
        return None
    finally:
        uploaded_file.seek(0)

    return None


def create_media_asset(
    *,
    uploaded_file,
    uploaded_by,
    title="",
    alt_text="",
    caption="",
):
    media_type, original_name, mime_type = inspect_media_upload(uploaded_file)
    extension = Path(original_name).suffix.lower()

    width = None
    height = None
    if media_type == MediaAsset.MediaType.IMAGE:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as image:
            width, height = image.size
        uploaded_file.seek(0)

    duration = _try_get_duration(uploaded_file, extension)

    # Keep the original name in DB, but save the physical file with a random safe name.
    uploaded_file.name = f"{uuid4().hex}{extension}"

    return MediaAsset.objects.create(
        uploaded_by=uploaded_by,
        file=uploaded_file,
        original_name=original_name,
        mime_type=mime_type,
        file_size=uploaded_file.size,
        media_type=media_type,
        width=width,
        height=height,
        duration=duration,
        title=title,
        alt_text=alt_text,
        caption=caption,
    )