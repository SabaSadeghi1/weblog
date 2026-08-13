from django import forms

from .models import BlogPost


class BlogPostForm(forms.ModelForm):

    cover_image = forms.ImageField(
        required=True
    )

    cover_alt = forms.CharField(
        max_length=255,
        required=False
    )


    class Meta:

        model = BlogPost

        fields = [
            'category',
            'title',
            'summary',
            'content',
            'seo_title',
            'seo_description',
        ]