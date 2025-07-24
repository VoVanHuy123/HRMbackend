from rest_framework import permissions
from employee.models import Employee

class IsAdmin(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.role != "Admin":
            return False

        return True

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if hasattr(user, 'role') and user.role == "Admin":
            return True
        return hasattr(user, 'employee') and obj.employee == user.employee