from django.conf import settings
from django.db import models
from django.utils.text import slugify

class BlogPost(models.Model):
    STATUS_CHOICES = (("draft","Draft"),("pending_review","Pending Review"),("approved","Approved"),("scheduled","Scheduled"),("published","Published"),("rejected","Rejected"),("archived","Archived"),)
    author_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="blog_posts",)
    category = models.ForeignKey("BlogCategory",on_delete=models.SET_NULL,null=True,blank=True,related_name="posts",)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270,unique=True,blank=True,allow_unicode=True,)
    summary = models.CharField(max_length=500,blank=True)
    content = models.TextField()
    status = models.CharField(max_length=30,choices=STATUS_CHOICES,default="draft")
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True,blank=True)
    seo_title = models.CharField(max_length=250,blank=True)
    seo_description = models.CharField(max_length=500,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField("BlogTag",through="BlogPostTag",related_name="posts",blank=True,)
    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title,allow_unicode=True,)
            slug = base_slug
            number = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                number += 1
                slug = f"{base_slug}-{number}"
            self.slug = slug
        super().save(*args, **kwargs)
    class Meta:
        db_table = "blog_posts"