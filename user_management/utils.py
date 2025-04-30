# utils.py
def get_user_roles(user):
    """Get all roles for a user including inherited roles"""
    roles = set(user.roles.all())
    
    # Add parent roles
    for role in list(roles):
        parent = role.parent
        while parent:
            roles.add(parent)
            parent = parent.parent
    
    return roles

def has_role(user, role_names):
    """Check if user has any of the specified roles"""
    return user.roles.filter(name__in=role_names).exists()

def has_permission(user, perm_codename):
    """Check if user has permission through any of their roles"""
    for role in get_user_roles(user):
        if role.permissions.filter(codename=perm_codename).exists():
            return True
    return False