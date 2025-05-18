from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.contrib.sitemaps.views import sitemap

# Sitemap imports
from jenga_home.sitemaps import BlogPostSitemap, StaticViewSitemap
from soma.sitemaps import CourseSitemap, LearningMaterialSitemap, SessionSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'blog': BlogPostSitemap,
    'courses': CourseSitemap,
    'materials': LearningMaterialSitemap,
    'sessions': SessionSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('jenga_home.urls', namespace='jenga_home')),
    path('', include('soma.urls')),
    path('', include('user_management.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('sitemap.xml/', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', include('jenga_home.urls')),  # We'll add this to jenga_home.urls
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'jenga_home.views.handler404'