from django.contrib import admin
from .models import (
    BlogPost, FeaturedLink, BlogCategory, Comment, 
    RequestType, FormRequest
)
from django_summernote.admin import SummernoteModelAdmin

class FeaturedLinkInline(admin.TabularInline):
    model = FeaturedLink
    extra = 1
    fields = ('title', 'url', 'is_external', 'order')

@admin.register(BlogPost)
class BlogPostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ('title', 'status', 'publish_date')
    list_filter = ('status', 'categories')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [FeaturedLinkInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'content')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'excerpt'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('status', 'publish_date', 'categories', 'tags')
        }),
        ('Media', {
            'fields': ('featured_image',)
        })
    )


# Register other models
admin.site.register(BlogCategory)
admin.site.register(Comment)
admin.site.register(RequestType)
admin.site.register(FormRequest)