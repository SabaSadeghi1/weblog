from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse

class BlogPost(models.Model):
    STATUS_CHOICES = (("draft","Draft"),("pending_review","Pending Review"),("approved","Approved"),("scheduled","Scheduled"),("published","Published"),("rejected","Rejected"),)
    author_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="blog_posts",)
    category = models.ForeignKey("BlogCategory",on_delete=models.PROTECT,related_name="posts",)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270,unique=True,blank=True,editable=False,allow_unicode=True,)
    summary = models.CharField(max_length=500)
    content = CKEditor5Field(config_name="extends")
    status = models.CharField(max_length=30,choices=STATUS_CHOICES,default="draft")
    is_featured = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True,blank=True)
    published_at = models.DateTimeField(null=True,blank=True,editable=False)
    seo_title = models.CharField(max_length=250,blank=True)
    seo_description = models.CharField(max_length=500,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField("BlogTag",through="BlogPostTag",related_name="posts",blank=True,)

    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse("blog:post_detail",kwargs={"slug":self.slug})

    def clean(self):
        errors = {}

        if self.status == "scheduled":
            if not self.scheduled_for:
                errors["scheduled_for"] = "Scheduled posts must have a publication date."
            elif self.scheduled_for <= timezone.now():
                errors["scheduled_for"] = "Scheduled publication must be in the future."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title,allow_unicode=True,) or "post"
            slug = base_slug
            number = 1

            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                number += 1
                slug = f"{base_slug}-{number}"

            self.slug = slug

        if self.status == "published":
            if not self.published_at:
                self.published_at = timezone.now()
            self.scheduled_for = None
        else:
            self.published_at = None

            if self.status != "scheduled":
                self.scheduled_for = None

        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "blog_posts"