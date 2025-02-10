from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
import re

from django.core.exceptions import ValidationError
from user.models import Users


User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    '''
    Сериализатор для пользователя
    '''
    is_subscribed = serializers.SerializerMethodField(default=False)

    class Meta(DjoserUserSerializer.Meta):
        model = Users
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )
        read_only_fields = ('id',)

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
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.follow_to.filter(user=request.user).exists()
        return False


class UserAvatarSerializer(serializers.Serializer):
    '''
    Сериализатор аватара польтзователя
    '''
    avatar = Base64ImageField(required=True)

    def update(self, instance, validated_data):
        if not validated_data.get('avatar'):
            raise serializers.ValidationError('Поле пусто')
        instance.avatar = validated_data.get('avatar')
        instance.save()
        return instance

    class Meta:
        model = Users
        fields = ('avatar',)
