from django.http import HttpResponse
from django.db.models import Sum
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from urlshortner.models import Url
from urlshortner.utils import shorten_url

from api.filters import RecipeFilter
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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthor, IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link',
            url_name='get-link', permission_classes=[AllowAny])
    def get_link(self, request, pk):
        '''
        Создание короткой ссылки
        '''
        main_domain = request.build_absolute_uri(
        ).replace(request.get_full_path(), '')
        url_route_to_recipe = main_domain + f'/recipes/{pk}/'
        short_url = Url.objects.filter(url=url_route_to_recipe).first()
        if short_url:
            short_link = main_domain.replace(
                request.get_full_path(), ''
            ) + '/s/' + short_url.short_url + '/'
            return Response({'short-link': short_link})
        url_route_to_recipe = shorten_url(
            url_route_to_recipe,
            is_permanent=False
        )
        short_link = main_domain.replace(
            request.get_full_path(), ''
        ) + '/s/' + url_route_to_recipe
        return Response({'short-link': short_link})


class FavoriteAndShoppingViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = Pagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthor, IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'], url_path='Favourite',
            permission_classes=[permissions.IsAuthenticated])
    def post_favourite(self, request, pk):
        return self.add_item_to_list(request.user, pk, 'Favourite')

    @post_favourite.mapping.delete
    def favourite_delete(self, request, pk):
        return self.remove_item_from_list(request.user, pk, 'Favourite')

    @action(detail=True, methods=['post'], url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def post_shopping_cart(self, request, pk):
        return self.add_item_to_list(request.user, pk, 'shopping_cart')

    @post_shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self.remove_item_from_list(request.user, pk, 'shopping_cart')

    def add_item_to_list(self, user, pk, list_type):
        try:
            if list_type == 'Favourite':
                serializer = FavouriteSerializer(
                    data={}, context={'request': self.request, 'id': pk})
                serializer.is_valid(raise_exception=True)
                favourite_item = serializer.create(serializer.validated_data)
                item_data = FavouriteAndShoppingCartSerializer(
                    favourite_item).data
            elif list_type == 'shopping_cart':
                serializer = ShoppingCartSerializer(
                    data={}, context={'request': self.request, 'id': pk})
                serializer.is_valid(raise_exception=True)
                shopping_cart_item = serializer.create(
                    serializer.validated_data)
                item_data = FavouriteAndShoppingCartSerializer(
                    shopping_cart_item).data
            return Response(item_data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError:
            return Response(
                {'error': str(serializers.ValidationError)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def remove_item_from_list(self, user, pk, list_type):
        try:
            if list_type == 'favorite':
                serializer = FavouriteSerializer(
                    context={'request': self.request, 'id': pk})
                serializer.delete(user)
            elif list_type == 'shopping_cart':
                serializer = ShoppingCartSerializer(
                    context={'request': self.request, 'id': pk})
                serializer.delete(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except serializers.ValidationError as e:
            return Response(
                {'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False, methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        if not ingredients.exists():
            return Response(
                {'errors': 'В корзине ничего нет.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_list_text = 'Список покупок:\n\n'
        for item in ingredients:
            shopping_list_text += (
                f'{item["ingredient__name"]}, '
                f'({item["ingredient__measurement_unit"]}) — '
                f'{item["total_amount"]}\n'
            )

        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'

        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
