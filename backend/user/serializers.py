from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
import re

from api.serializers import FavouriteAndShoppingCartSerializer
from django.core.exceptions import ValidationError
from user.models import Users, Follow


class UserSerializer(DjoserUserSerializer):
    '''
    Сериализатор для пользователя
    '''
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = Users
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')

    def validate_username(value):
        pattern = r'^[\w.@+-]+\Z'
        if value == "me":
            raise ValidationError(
                "Вы не можете выбрать никнейм 'me', "
                "выберите другой никнейм.")
        if not re.match(pattern, value):
            invalid_chars = re.sub(pattern, '', value)
            raise ValidationError(
                f'Введите корректный юзернейм.'
                f'Эти символы недопустимы: {invalid_chars}'
            )
        return value

    def get_is_subscribed(self, obj):
        try:
            return obj.is_subscribed
        except AttributeError:
            user = self.context['request'].user
            if user.is_anonymous:
                return False
            return obj.follow_to.filter(follower=user).exists()


class UserAvatarSerializer(serializers.ModelSerializer):
    '''
    Сериализатор аватара польтзователя
    '''
    avatar = Base64ImageField(required=True)

    class Meta:
        model = Users
        fields = ('avatar',)


class SubscribingSerializer(serializers.ModelSerializer):
    '''
    Сериализатор подписчиков
    '''

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = Users
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')
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
        return FavouriteAndShoppingCartSerializer(
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
        fields = ('user', 'subscribing',)
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
