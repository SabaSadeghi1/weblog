from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from blog import views
from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("posts/", include("blog.urls")),
    # path('blog/', views.post_list, name='post_list')
    path("", include("core.urls")),
    path('register/', accounts_views.user_register, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT,)



