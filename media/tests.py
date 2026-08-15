from django.test import TestCase



from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from PIL import Image

from blog.models import BlogCategory, BlogPost

from .models import BlogPostMedia
from .services import create_media_asset
from .validators import inspect_media_upload


def png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (1, 1), "white").save(buffer, format="PNG")
    return buffer.getvalue()



class MediaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="media-user",
            email="media@example.com",
            password="pass12345",
        )
        self.category = BlogCategory.objects.create(name="Tech")
        self.post = BlogPost.objects.create(
            author_user=self.user,
            category=self.category,
            title="Media post",
            summary="Summary",
            content="Content",
            status="published",
        )

    def test_valid_image_upload_records_metadata(self):
        uploaded = SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")
        asset = create_media_asset(uploaded_file=uploaded, uploaded_by=self.user)
        self.assertEqual(asset.media_type, "image")
        self.assertEqual(asset.original_name, "photo.png")
        self.assertEqual((asset.width, asset.height), (1, 1))
        self.assertNotEqual(asset.file.name.split("/")[-1], "photo.png")

    def test_disallowed_extension_is_rejected(self):
        uploaded = SimpleUploadedFile("payload.exe", b"MZ", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            inspect_media_upload(uploaded)

    def test_oversized_file_is_rejected(self):
        uploaded = SimpleUploadedFile("notes.txt", b"x", content_type="text/plain")
        uploaded.size = 21 * 1024 * 1024
        with self.assertRaises(ValidationError):
            inspect_media_upload(uploaded)

    def test_only_one_active_cover_per_post(self):
        asset1 = create_media_asset(
            uploaded_file=SimpleUploadedFile("a.png", png_bytes(), content_type="image/png"),
            uploaded_by=self.user,
        )
        asset2 = create_media_asset(
            uploaded_file=SimpleUploadedFile("b.png", png_bytes(), content_type="image/png"),
            uploaded_by=self.user,
        )
        BlogPostMedia.objects.create(
            post=self.post,
            media_asset=asset1,
            purpose=BlogPostMedia.Purpose.COVER,
            is_active=True,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BlogPostMedia.objects.create(
                    post=self.post,
                    media_asset=asset2,
                    purpose=BlogPostMedia.Purpose.COVER,
                    is_active=True,
                )

    def test_upload_endpoint_requires_login(self):
        response = self.client.post(
            "/media-api/upload/",
            {"file": SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")},
        )
        self.assertEqual(response.status_code, 302)

    def test_upload_endpoint_returns_asset_metadata(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/media-api/upload/",
            {"file": SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["media_type"], "image")
        self.assertTrue(payload["url"])
