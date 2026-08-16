from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("",views.post_list,name="post_list"),
    path("new/",views.post_create,name="post_create"),
    path("mine/",views.my_posts,name="my_posts"),
    path("edit/<int:id>/",views.post_update,name="post_update"),
    path("<str:slug>/",views.post_detail,name="post_detail"),
]