from django import forms
from django.core.exceptions import ValidationError

from media.validators import inspect_media_upload

from .models import BlogPost


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [
                single_file_clean(item, initial)
                for item in data
            ]

        if data:
            return [single_file_clean(data, initial)]

        return []


class BlogPostForm(forms.ModelForm):
    cover_image = forms.ImageField(
        required=True,
        help_text="Required. JPG, PNG, GIF or WebP; maximum 10 MB.",
    )

    summary = forms.CharField(
        min_length=100,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Write a summary between 100 and 500 characters.",
            }
        ),
        
        help_text="Summary must be between 100 and 500 characters.",
        error_messages={
            "min_length": "Summary must be at least 100 characters.",
            "max_length": "Summary cannot be more than 500 characters.",
            "required": "Please write a summary.",
        },
    )

    media_files = MultipleFileField(
        required=False,
        help_text=(
            "Optional. You can select multiple images, videos, "
            "audio files, documents, PDFs or other allowed files."
        ),
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": (
                    "image/*,video/*,audio/*,"
                    ".pdf,.doc,.docx,.odt,.xls,.xlsx,"
                    ".ppt,.pptx,.txt,.csv,.zip"
                ),
            }
        ),
    )

    class Meta:
        model = BlogPost

        fields = [
            "category",
            "title",
            "summary",
            "content",
        ]

    def clean_cover_image(self):
        cover_image = self.cleaned_data["cover_image"]

        media_type, _, _ = inspect_media_upload(
            cover_image
        )

        if media_type != "image":
            raise ValidationError(
                "The cover must be an image."
            )

        return cover_image

    def clean_media_files(self):
        media_files = self.cleaned_data.get(
            "media_files",
            [],
        )

        errors = []

        for uploaded_file in media_files:
            try:
                inspect_media_upload(uploaded_file)

            except ValidationError as exc:
                for message in exc.messages:
                    errors.append(
                        f"{uploaded_file.name}: {message}"
                    )

        if errors:
            raise ValidationError(errors)

        return media_files

class SchedulePostForm(forms.Form):
    scheduled_for = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}
        )
    )


class BlogPostEditForm(forms.ModelForm):

    class Meta:
        model = BlogPost
        fields = [
            "category",
            "title",
            "summary",
            "content",
        ]