from django.urls import include, path
from rest_framework.routers import DefaultRouter

from backend.api.recipes.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet
)
from backend.api.user.views import UsersViewSet

router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')

router.register

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
