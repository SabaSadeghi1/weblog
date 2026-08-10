from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save

class User(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to='profiles', null=True, blank=True)
    phone = models.CharField(max_length=14, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

def user_save_profile(sender, **kwargs):
        if kwargs['created']:
            profile_user = UserProfile(
                user = kwargs['instance']
            )

            profile_user.save()

post_save.connect(user_save_profile, sender=User)