from django.utils.deprecation import MiddlewareMixin
from user_management.utils import get_user_roles

class RBACMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # Get all roles (including inherited)
            request.user_roles = get_user_roles(request.user)
            print(f"User '{request.user.username}' has roles: {[role.name for role in request.user_roles]}")  # Debug
            
            # Add permission-checking logic to the request object
            request.has_perm = lambda perm: any(
                print(f"Checking permission '{perm}' in role '{role.name}'") or  # Debug
                role.permissions.filter(codename=perm).exists()
                for role in request.user_roles
            )