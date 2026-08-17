from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("new/", views.post_create, name="post_create"),

    path("mine/", views.my_posts, name="my_posts"),
    path("edit/<int:id>/", views.post_update, name="post_update"),

    path("editor/", views.editor_posts, name="editor_posts"),
    path("editor/<int:id>/", views.post_review, name="post_review"),

    path("<str:slug>/edit/", views.post_edit, name="post_edit"),
    path("<str:slug>/delete/", views.post_delete, name="post_delete"),

    path("<str:slug>/", views.post_detail, name="post_detail"),
]