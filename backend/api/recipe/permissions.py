from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsAuthor(permissions.BasePermission):
    """
    Доступ только автору и суперюзеру
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user
