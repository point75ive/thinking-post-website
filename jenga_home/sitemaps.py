from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost, BlogCategory

class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return [
            'jenga_home:home',
            'jenga_home:services',
            'jenga_home:about',
            'jenga_home:bda',
            'jenga_home:contact_page',
            'jenga_home:index'
        ]

    def location(self, item):
        return reverse(item)