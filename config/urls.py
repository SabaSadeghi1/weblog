from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from blog import views
from accounts import views as accounts_views
from django.contrib.sitemaps.views import sitemap
from seo import views as seo_views
from seo.feeds import LatestPostsFeed
from seo.sitemaps import (
    BlogPostSitemap,
    BlogCategorySitemap,
    AuthorSitemap,
)

sitemaps = {
    "posts": BlogPostSitemap,
    "categories": BlogCategorySitemap,
    "authors": AuthorSitemap,
}
urlpatterns = [
    path("admin/", admin.site.urls),
    path("posts/", include("blog.urls")),
    path("social/", include("social.urls")),
    path("media-api/", include("media.urls")),
    path('register/', accounts_views.user_register, name='register'),
    path("ckeditor5/",include("django_ckeditor_5.urls")),
    path('',include('discovery.urls')),
    path("", include("core.urls")),
    path("sitemap.xml",sitemap,{"sitemaps": sitemaps},name="django.contrib.sitemaps.views.sitemap",),
    path("robots.txt",seo_views.robots_txt,name="robots_txt"),
    path('login/',accounts_views.user_login,name='login'),
    path('logout/',accounts_views.user_logout,name='logout'),
    path('profile/',accounts_views.user_profile,name='profile'),
    path('profile/edit/',accounts_views.profile_update,name='profile_update'),
    path('author/<str:username>/',accounts_views.author_profile,name='author_profile'),
    path('rss/',LatestPostsFeed(),name='rss'),
    path('accounts/',include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT,)


