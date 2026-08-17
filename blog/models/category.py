from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

class BlogCategory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150,unique=True,blank=True,allow_unicode=True,)
    parent = models.ForeignKey("self",on_delete=models.SET_NULL,null=True,blank=True,related_name="children",)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=250,blank=True)
    seo_description = models.CharField(max_length=500,blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    def clean(self):
        if self.parent:
            if self.pk and self.parent.pk == self.pk:
                raise ValidationError({"parent":"کتگوری و پرنتش نباید بکی باشه."})
            parent = self.parent
            while parent:
                if self.pk and parent.pk == self.pk:
                    raise ValidationError({"parent":"حلقه ایجاد شد یه سطح برگشتیم عقب."})
                parent = parent.parent
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name,allow_unicode=True,)
            slug = base_slug
            number = 1
            while BlogCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                number += 1
                slug = f"{base_slug}-{number}"
            self.slug = slug
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "blog_categories"
        ordering = ["sort_order","name"]
