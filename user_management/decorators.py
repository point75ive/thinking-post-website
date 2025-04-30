from django.http import HttpResponseForbidden
from functools import wraps
from .utils import has_role, has_permission,get_user_roles


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and any(has_role(request.user, role) for role in roles):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this page.")
        return _wrapped_view
    return decorator

def permission_required(perm_codename):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.has_perm(perm_codename):
                return HttpResponseForbidden("You don't have required permission")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def category_required(*categories):
    """Ensures user has at least one role in the specified categories"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")
                
            user_roles = get_user_roles(request.user)
            if not any(role.category in categories for role in user_roles):
                return HttpResponseForbidden("You don't have access to this category")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator