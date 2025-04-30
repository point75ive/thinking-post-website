# models.py
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone



from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Add custom fields here (if any)
    
    objects = CustomUserManager()  # This is crucial
    
    # Your existing fields...
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to...",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )
    roles = models.ManyToManyField("Role", through="UserRole")

    def __str__(self):
        return self.username

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    permissions = models.ManyToManyField(Permission)
    is_supervisor = models.BooleanField(default=False)
    category = models.CharField(
        max_length=50,
        choices=(
            ("academic", "Academic"),
            ("admin", "Administrative"),
            ("boarding", "Boarding"),
            ("security", "Security"),
            ("accounting", "Accounting"),
            ("student", "Student"),
        ),
    )

    def get_all_permissions(self):
        perms = set(self.permissions.all())
        if self.parent:
            perms |= set(self.parent.get_all_permissions())
        return perms


class UserRole(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=True)


class AuditLogManager(models.Manager):
    def for_user(self, user):
        """Returns audit logs for a specific user."""
        return self.filter(user=user)


class AuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    model_affected = models.CharField(max_length=100)
    instance_id = models.PositiveIntegerField()

    objects = AuditLogManager()

    def __str__(self):
        return f"{self.user} - {self.action}"


class NotificationManager(models.Manager):
    def for_user(self, user):
        """Returns notifications for a specific user."""
        return self.filter(user=user)

    def unread(self):
        """Returns unread notifications."""
        return self.filter(read=False)


class Notification(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    link = models.URLField(blank=True, null=True)  # Optional link for the notification

    objects = NotificationManager()

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:50]}"

    class Meta:
        ordering = ["-created_at"]
