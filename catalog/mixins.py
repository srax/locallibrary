from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class ModeratorRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to moderators only."""
    
    def test_func(self):
        user = self.request.user
        # Check if user is authenticated and is a moderator
        if not user.is_authenticated:
            return False
        
        # Check if user has moderator profile flag or is in Moderators group
        try:
            return (user.profile.is_moderator or 
                    user.groups.filter(name='Moderators').exists())
        except:
            return False
    
    def handle_no_permission(self):
        # Don't show admin login, just deny access
        raise PermissionDenied("You must be a moderator to access this page.")


def is_moderator(user):
    """Helper function to check if a user is a moderator."""
    if not user.is_authenticated:
        return False
    try:
        return (user.profile.is_moderator or 
                user.groups.filter(name='Moderators').exists())
    except:
        return False
