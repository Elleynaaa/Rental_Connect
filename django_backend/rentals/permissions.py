from rest_framework import permissions

class IsLandlord(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == "landlord"
        )
    
class IsAdmin(permissions.BasePermission):
    """
    Allows access only to users whose profile role is 'admin'.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == "admin"
        )