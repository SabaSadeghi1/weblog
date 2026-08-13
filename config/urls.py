from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from blog import views
from accounts import views as accounts_views
from django.contrib.sitemaps.views import sitemap
from seo.sitemaps import BlogPostSitemap
from seo import views as seo_views

sitemaps = {
    "posts": BlogPostSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("posts/", include("blog.urls")),
    path('register/', accounts_views.user_register, name='register'),
    path("ckeditor5/",include("django_ckeditor_5.urls")),
    path("", include("core.urls")),
    path("sitemap.xml",sitemap,{"sitemaps": sitemaps},name="django.contrib.sitemaps.views.sitemap",),
    path("robots.txt",seo_views.robots_txt,name="robots_txt"),
    path('login/',accounts_views.user_login,name='login'),
    path('logout/',accounts_views.user_logout,name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT,)



