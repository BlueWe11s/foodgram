from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Tags, Ingredient, Recipe, RecipeIngredient
from user.serializers import UserSerializer
from user.models import Follower

User = get_user_model()


class FavouriteAndShoppingCrtSerializer(serializers.ModelSerializer):
    """Сериализация избранного и покупок."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализация тегов."""
    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class RecipeTagSerializer(serializers.ModelSerializer):
    """Сериализация тегов в рецептах."""
    class Meta:
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализация ингредиентов в рецептах."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(
        error_messages={
            'min_value': 'Количество не может быть меньше 1.'
        })

    class Meta:

        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class CreateIngredientInRecipeSerializer(serializers.ModelSerializer):
    """Создания ингредиента в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        error_messages={
            'does_not_exist': 'Такого ингредиента нет.'
        }
    )

    class Meta:

        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализация ингредиентов."""
    amount = RecipeIngredientSerializer(read_only=True)

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализация рецептов для записи."""
    ingredients = CreateIngredientInRecipeSerializer(
        many=True, source='recipe_ingredients', required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True)
    image = Base64ImageField(required=True, allow_null=True)
    author = UserSerializer(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
        )

    @staticmethod
    def _set_ingredients_and_tags(validated_data, recipe):
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient.get('ingredient'),
                amount=ingredient.get('amount'),
            ) for ingredient in ingredients
        )

    def create(self, validated_data):
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            image=validated_data.pop('image'),
            name=validated_data.pop('name'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time'), )
        self._set_ingredients_and_tags(
            validated_data,
            recipe
        )
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        self._set_ingredients_and_tags(
            validated_data,
            instance,
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data

    def validate(self, value):
        tags = value.get('tags')
        ingredients = value.get('recipe_ingredients')

        if not tags:
            raise serializers.ValidationError('Необходимо выбрать теги.')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужно выбрать ингредиенты.')

        return value

    def validate_tags(self, value):

        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не могут повторяться.')
        if len(value) < 1:
            raise serializers.ValidationError('Добавьте теги.')
        return value

    def validate_ingredients(self, value):
        ingredient_set = set()

        if len(value) < 1:
            raise serializers.ValidationError('Добавьте ингредиенты.')

        for item in value:
            item_tuple = tuple(sorted(item.items()))

            if item_tuple in ingredient_set:
                raise serializers.ValidationError(
                    'Ингредиенты не могут повторяться.')
            ingredient_set.add(item_tuple)

        return value


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализация рецептов для чтения."""
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(required=False)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
            'is_in_shopping_cart', 'is_favorited'
        )

    def get_user(self):
        request = self.context.get('request')
        return request.user if request else None

    def get_is_favorited(self, obj):
        user = self.get_user()
        if user and not user.is_anonymous:
            return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.get_user()
        if user and not user.is_anonymous:
            return obj.shopping_carts.filter(user=user).exists()
        return False


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализация подписок."""

    class Meta:
        model = Follower
        fields = ('user', 'subscribing',)
        validators = [
            UniqueTogetherValidator(
                fields=('user', 'subscribing'),
                queryset=model.objects.all(),
                message='Вы уже подписаны на этого пользователя.',
            )
        ]

    def validate_subscribing(self, data):

        if self.context.get('request').user == data:
            raise serializers.ValidationError(
                'Вы не можете подписаться сами на себя.'
            )
        return data

    def to_representation(self, instance):
        return SubscribingSerializer(
            instance.subscribing,
            context=self.context,
        ).data


class SubscribingSerializer(serializers.ModelSerializer):
    """Сериализация подписчика."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        return Follower.objects.filter(
            user=self.context['request'].user,
            subscribing=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        queryset = obj.recipes.all()
        limit = request.query_params.get('recipes_limit')
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except (TypeError, ValueError):
                pass
        return FavouriteAndShoppingCrtSerializer(
            queryset,
            many=True,
            context={'request': request},
        ).data


class BaseRecipeActionSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и корзины покупок."""

    class Meta:
        model = Recipe
        fields = ('id',)

    def validate(self, data):
        user = self.context['request'].user
        pk = self.context['id']
        recipe = get_object_or_404(Recipe, id=pk)

        if self._is_already_added(user, recipe):
            raise serializers.ValidationError(self.already_added_message)

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        pk = self.context['id']
        recipe = get_object_or_404(Recipe, id=pk)
        action_item = self._add_to_user_collection(user, recipe)
        return action_item.recipe

    def delete(self, user):
        pk = self.context['id']
        recipe = get_object_or_404(Recipe, id=pk)
        action_item = self._get_from_user_collection(user, recipe)

        if not action_item:
            raise serializers.ValidationError(self.already_removed_message)

        action_item.delete()


class FavouriteSerializer(BaseRecipeActionSerializer):
    """Сериализация избранного."""

    already_added_message = 'Рецепт уже был добавлен в избранное.'
    already_removed_message = 'Рецепт уже был удалён из избранного.'

    def _is_already_added(self, user, recipe):
        return recipe.favorites.filter(user=user).exists()

    def _add_to_user_collection(self, user, recipe):
        return user.favorites.create(recipe=recipe)

    def _get_from_user_collection(self, user, recipe):
        return user.favorites.filter(recipe=recipe).first()


class ShoppingCartSerializer(BaseRecipeActionSerializer):
    """Сериализация корзины покупок."""

    already_added_message = 'Рецепт уже был добавлен в корзину.'
    already_removed_message = 'Рецепт уже был удалён из корзины.'

    def _is_already_added(self, user, recipe):
        return recipe.shopping_carts.filter(user=user).exists()

    def _add_to_user_collection(self, user, recipe):
        return user.shopping_carts.create(recipe=recipe)

    def _get_from_user_collection(self, user, recipe):
        return user.shopping_carts.filter(recipe=recipe).first()