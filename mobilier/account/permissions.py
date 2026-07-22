from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """Permission pour l'administrateur uniquement."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsProprietaire(permissions.BasePermission):
    """Permission pour les propriétaires."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'PROPRIETAIRE')