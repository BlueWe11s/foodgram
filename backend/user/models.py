from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from user.constants import SLUG_LENGTH, EMAIL_LENGTH


class Users(AbstractUser):
    '''
    Модель Пользователей
    '''
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password',
    )
    first_name = models.CharField(
        'Имя',
        max_length=SLUG_LENGTH,
        unique=True,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=SLUG_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Логин',
        max_length=SLUG_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),)
    )
    email = models.EmailField(
        'Почта',
        max_length=EMAIL_LENGTH,
        unique=True,
    )
    avatar = models.ImageField(
        'Аватар',
        blank=True,
        null=True,
        upload_to='user/avatar/',
        default=''
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    '''
    Модель фолловеров
    '''
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
    )
    follow_to = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='follow_to',
        verbose_name='follow to',
    )

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'follow_to'],
                name='unique_follow',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.follow_to}'
