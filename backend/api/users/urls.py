from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.users.views import UsersViewSet

router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
