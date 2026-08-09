from django.db import models
from django.utils.text import slugify

class BlogCategory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150,unique=True,blank=True,allow_unicode=True,)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name,allow_unicode=True,)
            slug = base_slug
            number = 1
            while BlogCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                number += 1
                slug = f"{base_slug}-{number}"
            self.slug = slug
        super().save(*args, **kwargs)
    class Meta:
        db_table = "blog_categories"