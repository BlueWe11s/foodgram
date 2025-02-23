import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserSerializer
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tags)
from user.models import Follow, Users
from api.serializers import UserSerializer

User = get_user_model()


from user.models import Follow

class UserSerializer(DjoserSerializer):
    """
    Сериализатор для пользователя
    """

    is_subscribed = serializers.SerializerMethodField(default=False)

    class Meta(DjoserSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        )
        read_only_fields = ("id",)

    def validate_username(value):
        pattern = r"^[\w.@+-]+\Z"
        if value == "me":
            raise ValidationError(
                "Вы не можете выбрать никнейм 'me', "
                "выберите другой никнейм."
            )
        if not re.match(pattern, value):
            invalid_chars = re.sub(pattern, "", value)
            raise ValidationError(
                f"Введите корректный юзернейм."
                f"Эти символы недопустимы: {invalid_chars}"
            )
        return value

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return Follow.objects.filter(
            user=request.user.id, author=obj.id
        ).exists()


class UserAvatarSerializer(serializers.Serializer):
    """
    Сериализатор аватара польтзователя
    """

    avatar = Base64ImageField(required=True)

    def update(self, instance, validated_data):
        if not validated_data.get("avatar"):
            raise serializers.ValidationError("Поле пусто")
        instance.avatar = validated_data.get("avatar")
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ("avatar",)



class TagsSerializer(serializers.ModelSerializer):
    """
    Сериализатор тегов
    """

    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class RecipeTagsSerializer(serializers.ModelSerializer):
    """
    Сериализатор тегов в рецептах
    """

    class Meta:
        fields = "__all__"


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов
    """

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )
    amount = serializers.IntegerField(
        error_messages={"min_value": "Количество не может быть меньше 1."}
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов
    """

    amount = RecipeIngredientsSerializer(read_only=True)

    class Meta:
        model = Ingredient
        fields = "__all__"


class CreateIngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор создание ингредиентов
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
        error_messages={"does_not_exist": "Такого ингредиента не существует"},
    )

    class Meta:

        model = RecipeIngredient
        fields = (
            "id",
            "amount",
        )


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор рецептов
    """

    ingredients = CreateIngredientRecipeSerializer(
        many=True, source="recipe_ingredients"
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tags.objects.all(), required=True
    )
    image = Base64ImageField(required=True, allow_null=False)
    author = serializers.SlugRelatedField(
        slug_field="username", read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "author",
            "ingredients",
            "tags",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ["author"]

    def update_tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(recipe=recipe, **ingredient)
                for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("recipe_ingredients")
        validated_data.pop("author", None)
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        self.update_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("recipe_ingredients")
        self.update_tags_and_ingredients(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def validate(self, value):
        tags = value.get("tags")
        ingredients = value.get("recipe_ingredients")
        image = value.get("image")
        if not tags:
            raise serializers.ValidationError("Необходимо выбрать тэги")
        if not ingredients:
            raise serializers.ValidationError("Необходимо выбрать ингридиенты")
        if not image:
            raise serializers.ValidationError(
                "Необходимо загрузить изображение"
            )
        return value

    def validate_tags(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться")
        if len(value) < 1:
            raise serializers.ValidationError("Добавьте теги")
        return value

    def validate_ingredients(self, value):
        ingredient_set = set()
        if len(value) < 1:
            raise serializers.ValidationError("Добавьте ингредиенты")
        for item in value:
            item_tuple = tuple(sorted(item.items()))

            if item_tuple in ingredient_set:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться."
                )
            ingredient_set.add(item_tuple)
        return value

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор рецептов для чтения
    """

    ingredients = RecipeIngredientsSerializer(
        source="recipe_ingredients",
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
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_user(self):
        request = self.context.get("request")
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


class FavouriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели избранных рецептов
    """

    class Meta:
        model = FavoriteRecipe
        fields = ("user", "recipe")

    def validate(self, data):
        if FavoriteRecipe.objects.filter(**data).exists():
            raise serializers.ValidationError(
                "Рецепт уже добавлен в избранное"
            )
        return data

    def to_representation(self, instance):
        return CartsSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели корзины
    """

    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")

    def validate(self, data):
        if ShoppingCart.objects.filter(**data).exists():
            raise serializers.ValidationError(
                "Рецепт уже добавлен в список покупок"
            )
        return data

    def to_representation(self, instance):
        return CartsSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data


class CartsSerializer(serializers.ModelSerializer):
    """
    Сериализатор избранного и корзины
    """

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class SubscribingSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписчиков
    """

    is_subscribed = serializers.SerializerMethodField(default=False)
    recipes = serializers.SerializerMethodField(method_name="get_recipes")
    recipes_count = serializers.ReadOnlyField(default=0)

    class Meta:
        model = Users
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("id",)

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=self.context["request"].user, author=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context["request"]
        queryset = obj.recipes.all()
        limit = request.query_params.get("recipes_limit")
        if limit:
            try:
                queryset = queryset[: int(limit)]
            except (TypeError, ValueError):
                pass
        return CartsSerializer(
            queryset,
            many=True,
            context={"request": request},
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписок
    """

    class Meta:
        model = Follow
        fields = ("user", "author")

    def validate(self, data):
        user = data["user"]
        author = data["author"]
        if user == author:
            raise serializers.ValidationError(
                "Вы не можете подписаться на себя"
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Вы уже подписаны")
        return data

    def to_representation(self, instance):
        return SubscribingSerializer(
            instance.author,
            context=self.context,
        ).data
