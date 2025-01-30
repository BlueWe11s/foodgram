from django.http import HttpResponse
from django.db.models import Sum
from rest_framework import permissions, serializers, status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from urlshortner.models import Url
from urlshortner.utils import shorten_url

from api.filters import IngredientFilter, RecipeFilter
from recipes.permissions import IsAuthor
from api.serializers import (
    FavouriteAndShoppingCartSerializer,
    FavouriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Tags
)
from user.views import Pagination


class RecipesViewSet(viewsets.GenericViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthor, IsAuthenticatedOrReadOnly]
