from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint

from user.models import Users
from recipes.constants import NAME_LENGTH, SLUG_LENGTH, SI_LENGTH, MIN_COOKING_TIME

User = Users


class Tags(models.Model):
    '''
    Модель тегов
    '''
    name = models.CharField(
        'Наименование',
        max_length=NAME_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный идентификатор',
        max_length=SLUG_LENGTH,
        unique=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    '''
    Модель ингредиентов
    '''
    name = models.CharField('Наименование', max_length=NAME_LENGTH)
    measurement_unit = models.CharField('Единица измерения', max_length=SI_LENGTH)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['user', 'measurement_unit'],
                name = 'unique_name_measurement'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    '''
    Модель рецептов
    '''

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
        )
    name = models.CharField(
        'Наименование',
        max_length=NAME_LENGTH
    )
    image = models.ImageField('Изображение')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Список тегов',
        related_name='recipes'
    )
    cooking_time = models.models.PositiveSmallIntegerField(
        'Время приготовления рецепта',
        validators=[MinValueValidator(MIN_COOKING_TIME)]
        )
    slug = models.SlugField(
        'Уникальный идентификатор',
        max_length=SLUG_LENGTH,
        unique=True
        )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class FavoriteRecipe(models.Model):
    '''
    Модель любимых рецептов
    '''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        db_index=True
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_recipe',
            ),
        ]


class ShoppingCart(models.Model):
    '''
    Модель корзины
    '''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        db_index=True,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт'
        on_delete=models.CASCADE,
    )

    class Meta:
        default_related_name = 'shoping_carts'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_recipe',
            ),
        ]
