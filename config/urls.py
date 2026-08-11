from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from blog import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path('blog/', views.post_list, name='post_list'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT,)