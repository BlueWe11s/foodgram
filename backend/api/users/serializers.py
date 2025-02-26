from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from djoser.serializers import UserSerializer as DjoserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from user.models import Follow
from api.serializers import CartsSerializer

User = get_user_model()


class UserSerializer(DjoserSerializer):
    """
    Сериализатор для пользователя
    """

    is_subscribed = serializers.SerializerMethodField(default=False)

    username_validator = UnicodeUsernameValidator()

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

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return request.user.follower.filter(author=obj).exists()


class UserAvatarSerializer(serializers.Serializer):
    """
    Сериализатор аватара польтзователя
    """

    avatar = Base64ImageField(required=True)

    def update(self, instance, validated_data):
        if not validated_data.get("avatar"):
            raise ValidationError("Поле пусто")
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
        request = self.context.get("request")
        return request.user.follower.filter(author=obj).exists()

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
            raise ValidationError(
                "Вы не можете подписаться на себя"
            )
        if user.follower.filter(author=author).exists():
            raise ValidationError("Вы уже подписаны")
        return data

    def to_representation(self, instance):
        return SubscribingSerializer(
            instance.author,
            context=self.context,
        ).data
