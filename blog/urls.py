from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("new/", views.post_create, name="post_create"),
    path("<str:slug>/edit/", views.post_edit, name="post_edit"),
    path("<str:slug>/delete/", views.post_delete, name="post_delete"),
    path("<str:slug>/", views.post_detail, name="post_detail"),
]