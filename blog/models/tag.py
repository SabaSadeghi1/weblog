from django.db import models
from django.utils.text import slugify

class BlogTag(models.Model):
    name = models.CharField(max_length=100,unique=True,)
    slug = models.SlugField(max_length=120,unique=True,blank=True,allow_unicode=True,)
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
            while BlogTag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                number += 1
                slug = f"{base_slug}-{number}"
            self.slug = slug
        super().save(*args, **kwargs)
    class Meta:
        db_table = "blog_tags"
class BlogPostTag(models.Model):
    post = models.ForeignKey("BlogPost",on_delete=models.CASCADE,related_name="post_tags",)
    tag = models.ForeignKey(BlogTag,on_delete=models.CASCADE,related_name="post_tags",)
    def __str__(self):
        return f"{self.post} - {self.tag}"

    class Meta:
        db_table = "blog_post_tags"
        constraints = [models.UniqueConstraint(fields=["post","tag"],name="unique_post_tag",)]