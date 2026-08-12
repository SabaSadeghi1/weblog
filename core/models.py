from django.db import models
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field

class SiteSettings(models.Model):
    singleton_key = models.CharField(max_length=20, default='global', unique=True)
    site_name = models.CharField(max_length=100)
    site_description = CKEditor5Field(config_name="extends",null=True, blank=True)
    default_seo_title = models.CharField(max_length=200, null=True, blank=True)
    default_seo_description =CKEditor5Field(config_name="extends",null=True, blank=True)
#    registration_enabled = models.BooleanField(default=True)
    comments_approval = models.BooleanField(default=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    def __str__(self):
      return self.site_name
