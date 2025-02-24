import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from djoser.serializers import UserSerializer as DjoserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Recipe
from user.models import Follow

User = get_user_model()


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


class SubscribingSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписчиков
    """

    is_subscribed = serializers.SerializerMethodField(default=False)
    recipes = serializers.SerializerMethodField(method_name="get_recipes")
    recipes_count = serializers.ReadOnlyField(default=0)

    class Meta:
        model = User
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
