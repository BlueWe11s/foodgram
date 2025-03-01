from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.recipe.views import IngredientViewSet, RecipeViewSet, TagViewSet


router = DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
urlpatterns = [
    path('', include(router.urls)),
]
