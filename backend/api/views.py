from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.serializers import (FavouriteSerializer, IngredientsSerializer,
                             RecipeReadSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagsSerializer,
                             SubscribeSerializer, SubscribingSerializer)
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tags)
from api.permissions import IsAuthor
from api.paginations import Pagination
from api.serializers import UserAvatarSerializer, UserSerializer
from user.models import Follow


User = get_user_model()


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = Pagination

    @action(
        methods=["get"],
        detail=False,
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscriptions",
        url_name="subscriptions",
    )
    def get_subscribe(self, request):
        """Получить список подписок пользователя."""
        user = request.user
        subscriptions = Follow.objects.filter(user=user)
        authors = [subscription.author for subscription in subscriptions]
        pages = self.paginate_queryset(authors)
        serializer = SubscribingSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscribe",
    )
    def post_subscribe(self, request, id):
        """Подписаться или отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={"user": user.id, "author": author.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        return Response(
            SubscribeSerializer(
                subscription, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @post_subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Подписаться или отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, id=id)
        deleted_count, _ = Follow.objects.filter(
            user=user, author=author
        ).delete()
        if not deleted_count:
            return Response(
                {"errors": "Вы не подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        url_path="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite_post(self, request, id):
        return self.add_item_to_list(request.user, id, "favorite")

    @favorite_post.mapping.delete
    def favorite_delete(self, request, id):
        return self.remove_item_from_list(request.user, id, "favorite")

    @action(
        detail=False,
        methods=["put"],
        url_path="me/avatar",
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_avatar(self, request):
        user = request.user

        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @get_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(
                {"status": "Аватар удален."}, status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"errors": "Такого объекта не существует."},
            status=status.HTTP_404_NOT_FOUND,
        )


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
        short_link = f'{request.get_full_path()}'[:-10]
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        methods=["post", "delete"],
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

    @action(
        methods=["post", "delete"],
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
        if request.method == "POST":
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
        elif request.method == "DELETE":
            deleted_count, _ = model.objects.filter(
                recipe__id=pk, user=user
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
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
