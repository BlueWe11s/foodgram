from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.recipe.filters import IngredientFilter, RecipeFilter
from api.recipe.serializers import (
    FavouriteSerializer,
    IngredientsSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagsSerializer
)
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tags
)
from api.recipe.permissions import IsAuthor
from api.paginations import Pagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    filterset_fields = ("author", "tags")
    pagination_class = Pagination
    permission_classes = [IsAuthor, IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk):
        return Response(
            {'short-link': f'{request.get_full_path()}'[:-10]},
            status=status.HTTP_200_OK
        )

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path="favorite",
        url_name="favorite",
    )
    def favourite(self, request, pk):
        """Добавляет или удаляет рецепт из избранного пользователя."""
        return self.action_with_favoutite_and_shop(
            request=request,
            pk=pk,
            model=FavoriteRecipe,
            serializer_class=FavouriteSerializer,
            message="{} уже в избранном.",
        )

    @favourite.mapping.delete
    def delete_favourite(self, request, pk):
        return self.delete_fovourite_and_shop(
            request=request,
            pk=pk,
            model=FavoriteRecipe,
        )

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk):
        return self.action_with_favoutite_and_shop(
            request=request,
            pk=pk,
            model=ShoppingCart,
            serializer_class=ShoppingCartSerializer,
            message="{} уже добавлен",
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_fovourite_and_shop(
            request=request,
            pk=pk,
            model=ShoppingCart,
        )

    def action_with_favoutite_and_shop(
        self,
        request,
        pk,
        model,
        serializer_class,
        message,
    ):
        """Добавляет/удаляет рецепты в избранное или корзину пользователя."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response(
                {"detail": message.format(recipe.name)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = serializer_class(
            data={"recipe": recipe.id, "user": user.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_fovourite_and_shop(
        self,
        request,
        pk,
        model,
    ):
        deleted_count, _ = model.objects.filter(
            recipe__id=pk, user=request.user
        ).delete()
        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not Recipe.objects.filter(id=pk).exists():
            return Response(
                {"detail": "Рецепта не существует"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"detail": "Рецепта нет в списке"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_carts__user=request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
        )
        if not ingredients.exists():
            return Response(
                {"errors": "В корзине ничего нет."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shopping_list_text = "Список покупок:\n\n"
        for item in ingredients:
            shopping_list_text += (
                f'{item["ingredient__name"]}, '
                f'({item["ingredient__measurement_unit"]}) — '
                f'{item["total_amount"]}\n'
            )
        response = HttpResponse(shopping_list_text, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    filterset_class = IngredientFilter
    search_fields = ('^name',)
