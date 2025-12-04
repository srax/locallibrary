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


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to staff members only."""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_staff
    
    def handle_no_permission(self):
        raise PermissionDenied("You must be a staff member to access this page.")


def is_staff_member(user):
    """Helper function to check if a user is a staff member."""
    return user.is_authenticated and user.is_staff
