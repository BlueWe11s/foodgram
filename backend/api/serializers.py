from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import ValidationError

from recipes.models import Tags, Ingredient, Recipe, RecipeIngredient
from user.serializers import UserSerializer
from api.mixins import RecipeActionMixin
from user.models import Users, Follow

User = get_user_model()


class TagsSerializer(serializers.ModelSerializer):
    '''
    Сериализатор тегов
    '''

    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug')


class RecipeTagsSerializer(serializers.ModelSerializer):
    '''
    Сериализатор тегов в рецептах
    '''

    class Meta:
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    '''
    Сериализатор ингредиентов
    '''

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


class IngredientsSerializer(serializers.ModelSerializer):
    '''
    Сериализатор ингредиентов
    '''

    amount = RecipeIngredientsSerializer(read_only=True)

    class Meta:
        model = Ingredient
        fields = '__all__'


class CreateIngredientRecipeSerializer(serializers.ModelSerializer):
    '''
    Сериализатор создание ингредиентов
    '''

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        error_messages={
            'does_not_exist': 'Такого ингредиента не существует'
        }
    )

    class Meta:

        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    '''
    Сериализатор рецептов
    '''

    ingredients = CreateIngredientRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all(),
        required=True
    )
    image = Base64ImageField(
        required=True,
        allow_null=False
    )
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        read_only_fields = ['author']

    def to_internal_value(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        internal_data = super().to_internal_value(data)
        internal_data['tags'] = tags
        internal_data['ingredients'] = ingredients
        return internal_data

    @staticmethod
    def update_tags_and_ingredients(validated_data, recipe):
        """Обновляет теги и ингредиенты для рецепта."""
        ingredients = validated_data.pop('recipe_ingerients', [])
        tags = validated_data.pop('tags', [])
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.get(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        """Создает новый рецепт с привязкой тегов и ингредиентов."""
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            image=validated_data.pop('image'),
            name=validated_data.pop('name'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time'), )
        self.update_tags_and_ingredients(
            validated_data,
            recipe
        )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт с возможностью изменить теги и ингредиенты."""
        instance.ingredients.clear()
        instance.tags.clear()
        self.update_tags_and_ingredients(
            validated_data,
            instance,
        )
        return super().update(instance, validated_data)

    # def validate(self, value):
    #     tags = value.get('tags')
    #     ingredients = value.get('recipes')

    #     if not tags:
    #         raise serializers.ValidationError('Нужно выбрать теги')
    #     if not ingredients:
    #         raise serializers.ValidationError(
    #             'Нужно выбрать ингредиенты'
    #         )
    #     return value


class RecipeReadSerializer(serializers.ModelSerializer):
    '''
    Сериализатор рецептов для чтения
    '''

    ingredients = RecipeIngredientsSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    tags = TagsSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
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


class FavouriteSerializer(RecipeActionMixin):
    '''
    Сериализатор избранного
    '''

    added_message = 'Рецепт уже был добавлен в избранное'
    removed_message = 'Рецепт уже был удалён из избранного'

    def added(self, user, recipe):
        return recipe.favorites.filter(user=user).exists()

    def add_to_user_collection(self, user, recipe):
        return user.favorites.create(recipe=recipe)

    def get_from_user_collection(self, user, recipe):
        return user.favorites.filter(recipe=recipe).first()


class ShoppingCartSerializer(RecipeActionMixin):
    '''
    Серилизатор корзины
    '''

    added_message = 'Рецепт уже был добавлен в корзину'
    removed_message = 'Рецепт уже был удалён из корзины'

    def added(self, user, recipe):
        return recipe.shopping_carts.filter(user=user).exists()

    def add_to_user_collection(self, user, recipe):
        return user.shopping_carts.create(recipe=recipe)

    def get_from_user_collection(self, user, recipe):
        return user.shopping_carts.filter(recipe=recipe).first()


class CartsSerializer(serializers.ModelSerializer):
    '''
    Сериализатор избранного и корзины
    '''

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribingSerializer(serializers.ModelSerializer):
    '''
    Сериализатор подписчиков
    '''

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = Users
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=self.context['request'].user,
            subscribing=obj).exists()

    def get_recipes(self, obj):
        request = self.context['request']
        queryset = obj.recipes.all()
        limit = request.query_params.get('recipes_limit')
        if limit:
            try:
                queryset = queryset[:int(limit)]
            except (TypeError, ValueError):
                pass
        return CartsSerializer(
            queryset,
            many=True,
            context={'request': request},
        ).data


class SubscribeSerializer(serializers.ModelSerializer):
    '''
    Сериализатор подписок
    '''

    class Meta:
        model = Follow
        fields = (
            'user',
            'subscribing',
        )
        validators = [
            UniqueTogetherValidator(
                fields=('user', 'subscribing'),
                queryset=model.objects.all(),
                message='Вы уже подписаны на этого пользователя',
            )
        ]

    def validate_subscribing(self, data):

        if self.context['request'].user == data:
            raise serializers.ValidationError(
                'Вы не можете подписаться сами на себя'
            )
        return data

    def to_representation(self, instance):
        return SubscribingSerializer(
            instance.subscribing,
            context=self.context,
        ).data
