from django.db import models

class BlogCategory(models.Model):

    name = models.CharField(max_length=150) #نام هر دسته رو مشخص میکنیم
    slug = models.SlugField(max_length=170,unique=True,blank=True,allow_unicode=True,)
    parent = models.ForeignKey("self",on_delete=models.PROTECT,null=True,blank=True,related_name="children",)
    description = models.TextField(blank=True,)
    order = models.PositiveIntegerField(default=0,)
    is_active = models.BooleanField(default=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    