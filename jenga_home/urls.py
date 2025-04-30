from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from jenga_home.sitemaps import BlogSitemap
from django.conf.urls.static import static
from .views import (
    home,
    services,
    about,
    index,
    post_detail,
    like_post,
    tag_view,
    bda, 
    contact_page,
    contact_success,
    author_posts,
    add_comment,
)

sitemaps = {
    "blog": BlogSitemap,
}


app_name = "jenga_home"


urlpatterns = [
    path("", home, name="home"),
    path("services", services, name="services"),
    path("about", about, name="about"),
    path("bda", bda, name="bda"),
    path('contact/', contact_page, name='contact_page'),
    path('contact/success/', contact_success, name='contact_success'),
    path('post', index, name='index'),
    path('post/<slug:slug>/', post_detail, name='post_detail'),
    path('post/<int:post_id>/comment/', add_comment, name='add_comment'),
    path('post/<int:post_id>/like/', like_post, name='like_post'),
    path('tags/<slug:slug>/', tag_view, name='tag'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('author/<str:username>/', author_posts, name='author_posts'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



