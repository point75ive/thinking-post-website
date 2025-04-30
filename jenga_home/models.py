from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django_resized import ResizedImageField
from taggit.managers import TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase
import json
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.contrib.auth import get_user_model
from django_summernote.fields import SummernoteTextField
from django_summernote.models import AbstractAttachment


# Central Base Model (Reusable)
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True



# Blog Models
class BlogCategory(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name

class FeaturedLink(BaseModel):
    blog_post = models.ForeignKey(
        "BlogPost", on_delete=models.CASCADE, related_name="featured_links"
    )
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    order = models.PositiveIntegerField(default=0)
    is_external = models.BooleanField(
        default=True, help_text="Opens in new tab if True"
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} → {self.url}"



class BlogPost(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("scheduled", "Scheduled"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    excerpt = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    publish_date = models.DateTimeField(db_index=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    categories = models.ManyToManyField(BlogCategory, blank=True)
    tags = TaggableManager(blank=True)
    related_posts = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        verbose_name="Manually curated related posts",
    )
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    featured_image = ResizedImageField(
        upload_to="blog/featured/%Y/%m/",
        size=[1200, 630],
        quality=80,
        blank=True,
        help_text="Optimal size: 1200x630px (2:1 ratio)",
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="liked_posts", blank=True
    )


    class Meta:
        ordering = ["-publish_date"]
        indexes = [
            models.Index(fields=["slug", "status"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()  # Always call super().clean() first

        if not self.slug:
            raise ValidationError("Slug is required")

    def save(self, *args, **kwargs):
        if self.status == "published" and not self.publish_date:
            self.publish_date = timezone.now()

        super().save(*args, **kwargs)

    def get_auto_related_posts(self):
        """Fallback: Returns related posts based on shared tags (excludes self)"""
        return (
            BlogPost.objects.filter(tags__in=self.tags.all(), status="published")
            .exclude(id=self.id)
            .distinct()[:5]
        )  # Limit to 5 posts

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.excerpt or self.content[:160]

    def get_absolute_url(self):
        return reverse("jenga_home:post_detail", kwargs={"slug": self.slug})

class SummernoteAttachment(AbstractAttachment):
    """
    Custom attachment model for Summernote with additional fields if needed
    """
    # Add any custom fields here if needed
    # For example:
    # description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Summernote Attachment'
        verbose_name_plural = 'Summernote Attachments'

    def __str__(self):
        return self.name if self.name else self.file.name

class Comment(BaseModel):
    blog_post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)
    content = models.TextField()
    is_public = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    """def clean(self, *args, **kwargs):
        if not self.user and (not self.name or not self.email):
            raise ValidationError(
                _("Name and email are required for anonymous comments.")
            )
        if 'styles' in kwargs:
            print(f"clean() method called with styles argument: {kwargs['styles']}")"""
   

    def __str__(self):
        return f"Comment by {self.user.username if self.user else self.name}"

# Form Request Models
class RequestType(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

class FormRequest(BaseModel):
    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    request_type = models.ForeignKey(RequestType, on_delete=models.CASCADE)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = PhoneNumberField(blank=True)
    company = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.request_type.name} request from {self.user if self.user else self.name}"