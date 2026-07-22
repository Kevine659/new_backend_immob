
from rest_framework.permissions import BasePermission

class IsAdminOrStaffUser(BasePermission):
    """
    Permission personnalisée pour accorder l'accès uniquement 
    aux superutilisateurs ou aux membres de l'équipe (staff).
    """
    def has_permission(self, request, view):
        # 1. Vérifier si l'utilisateur est bien connecté
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 2. Vérifier si l'utilisateur est un superuser ou un membre du staff
        return request.user.is_superuser or request.user.is_staff
    
from rest_framework import permissions

class IsAdminOrOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # COMPARER L'ID DU USER LIÉ AU PROFIL
        # obj.bailleur est un 'Profile', donc obj.bailleur.user est le 'User'
        is_owner = (obj.bailleur.user == request.user)
        is_admin = request.user.is_staff or request.user.is_superuser
        
        return is_admin or is_owner