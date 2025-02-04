from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
import re

from django.core.exceptions import ValidationError
from user.models import Users


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
