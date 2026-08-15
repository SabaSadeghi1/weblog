from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import create_media_asset


@login_required(login_url="login")
@require_POST
def upload_media(request):
    uploaded_file = request.FILES.get("file")

    if uploaded_file is None:
        return JsonResponse(
            {
                "ok": False,
                "errors": ["No file was uploaded."],
            },
            status=400,
        )

    try:
        asset = create_media_asset(
            uploaded_file=uploaded_file,
            uploaded_by=request.user,
            title=request.POST.get("title", "").strip(),
            alt_text=request.POST.get("alt_text", "").strip(),
            caption=request.POST.get("caption", "").strip(),
        )

    except ValidationError as exc:
        return JsonResponse(
            {
                "ok": False,
                "errors": exc.messages,
            },
            status=400,
        )

    return JsonResponse(
        {
            "ok": True,
            "id": asset.pk,
            "url": asset.file.url,
            "media_type": asset.media_type,
            "original_name": asset.original_name,
            "mime_type": asset.mime_type,
            "file_size": asset.file_size,
            "width": asset.width,
            "height": asset.height,
            "duration": asset.duration,
        },
        status=201,
    )
