from django.contrib.sitemaps import Sitemap
from .models import Course, Session, LearningMaterial

class CourseSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Course.objects.filter(is_deleted=False)

    def lastmod(self, obj):
        return obj.updated_at

class LearningMaterialSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return LearningMaterial.objects.filter(is_deleted=False)

class SessionSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Session.objects.filter(is_deleted=False)