from django.urls import path

from . import views

app_name = "social"

urlpatterns = [
    path("posts/<int:post_id>/comments/", views.comment_create, name="comment_create"),
    path("comments/<int:comment_id>/edit/", views.comment_edit, name="comment_edit"),
    path("posts/<int:post_id>/reaction/", views.reaction_toggle, name="reaction_toggle"),
    path("posts/<int:post_id>/bookmark/", views.bookmark_toggle, name="bookmark_toggle"),
    path("reports/", views.report_content, name="report_content"),
]