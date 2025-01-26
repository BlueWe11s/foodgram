from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Права на выполнение действий для админа
    и разрешенный просмотр для остальных
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )


class IsAdminorIsModerorIsSuperUser(BasePermission):
    """
    Права на редактирование всем кроме анона
    """
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if (
            request.user.is_authenticated
            and (
                request.user.is_admin
                or request.user.is_moderator
            )
        ):
            return True
        return (
            obj.author == request.user
        )


class IsAdminOnly(BasePermission):
    """
    Права на выполнение администратором и суперюзером
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )