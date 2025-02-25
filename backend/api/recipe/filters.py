from django_filters import rest_framework as filters

from recipes.models import Tags, User, Ingredient


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов
    """

    author = filters.ModelChoiceFilter(
        field_name="author_id",
        queryset=User.objects.all(),
    )
    tags = filters.filters.ModelMultipleChoiceFilter(
        queryset=Tags.objects.all(),
        field_name="tags__slug",
        to_field_name="slug",
    )
    is_favorited = filters.BooleanFilter(method="favorited_filter")
    is_in_shopping_cart = filters.BooleanFilter(method="shoppingcart_filter")

    def favorited_filter(self, queryset, name, value):
        if value is True and self.request.user.is_authenticated:
            return queryset.filter(favorites__user_id=self.request.user.id)
        return queryset

    def shoppingcart_filter(self, queryset, name, value):
        if value is True and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_carts__user_id=self.request.user.id
            )
        return queryset


class IngredientFilter(filters.FilterSet):
    """
    Фильтр для ингредиентов
    """

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
