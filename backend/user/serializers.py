from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.db import IntegrityError
from rest_framework import serializers

from recipes.serializers import RecipeSerializer
from user.validator import validate_username
from user.models import Follow
from recipes.constants import NAME_LENGTH

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    '''
    Сериализатор для пользователя
    '''

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed',)

    def get_is_subscribed(self, obj):
        try:
            return obj.is_subscribed
        except AttributeError:
            user = self.context['request'].user
            if user.is_anonymous:
                return False
            return obj.follow_to.filter(follower=user).exists()


class FollowToSerializer(UserSerializer):
    '''
    Сериализатор для подписчиков
    '''

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        requests = self.context['request']
        recipes = obj.recipes.all()

        limit = requests.query_params.get('recipes_limit')
        if limit is not None:
            try:
                recipes = obj.recipes.all()[: int(limit)]
            except ValueError:
                pass

        fields = ('id', 'name', 'image', 'cooking_time')
        return RecipeSerializer(recipes, many=True, fields=fields).data

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    '''
    Сериализатор для подписчиков
    '''

    follower = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Follow
        fields = ('follower', 'follow_to')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['follower', 'follow_to'],
                message='You are already a follower.',
            )
        ]

    def validate(self, attrs):
        if attrs['follow_to'] == attrs['follower']:
            raise serializers.ValidationError(
                'You cannot follow to yourself.',
            )
        return attrs


class AuthSerializer(serializers.Serializer):
    '''
    Сериализатор для обработки запроса на получени кода подтверждения
    '''
    email = serializers.EmailField(required=True, max_length=NAME_LENGTH)
    password = serializers.CharField()


    def validate(self, data):
        User.objects.get(
            password=data.get('password'),
            email=data.get('email')
        )
        return data


class TokenSerializer(serializers.Serializer):
    """
    Сериализатор для обработки
    """
    username = serializers.CharField()
    confirmation_code = serializers.CharField()
