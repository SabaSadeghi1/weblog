from django.urls import path
from . import views


app_name = 'discovery'


urlpatterns = [

    path(
        'trending/',
        views.trending_posts,
        name='trending'
    ),

    path(
        'feed/',
        views.personalized_feed,
        name='feed'
    ),

]