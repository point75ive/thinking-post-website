# learning/templatetags/rbac_tags.py
from django import template

register = template.Library()

@register.filter(name='has_perm')
def has_perm(request, perm_codename):
    """Check if the user has the specified permission."""
    return request.has_perm(f'learning.{perm_codename}')

@register.filter(name='has_role')
def has_role(user, role_name):
    """Check if the user has the specified role."""
    return user.roles.filter(name=role_name).exists()