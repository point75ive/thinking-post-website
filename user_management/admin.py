from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role, UserRole

class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1

class CustomUserAdmin(UserAdmin):
    inlines = [UserRoleInline]
    list_display = ('username', 'email', 'get_roles')
    
    def get_roles(self, obj):
        return ", ".join([r.name for r in obj.roles.all()])
    get_roles.short_description = 'Roles'

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'parent', 'is_supervisor')
    list_filter = ('category', 'is_supervisor')
    filter_horizontal = ('permissions',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Role.objects.exclude(id=request.resolver_match.kwargs.get('object_id'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Role, RoleAdmin)