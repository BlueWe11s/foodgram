from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint

from recipes.constants import (
    NAME_LENGTH,
    SLUG_LENGTH,
    SI_LENGTH,
    MIN_COOKING_TIME,
    MIN_AMOUNT,
)

User = get_user_model()


class Tags(models.Model):
    """
    Модель тегов
    """

    name = models.CharField(
        "Наименование", max_length=NAME_LENGTH, unique=True
    )
    slug = models.SlugField(
        "Уникальный идентификатор", max_length=SLUG_LENGTH, unique=True
    )

    class Meta:
        ordering = [
            "name",
        ]
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Модель ингредиентов
    """

    name = models.CharField("Наименование", max_length=NAME_LENGTH)
    measurement_unit = models.CharField(
        "Единица измерения", max_length=SI_LENGTH
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredients"
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель рецептов
    """

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Автор рецепта"
    )
    name = models.CharField("Наименование", max_length=NAME_LENGTH)
    image = models.ImageField(
        "Изображение",
        upload_to="recipes/images/",
    )
    text = models.TextField("Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингридиенты",
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name="Список тегов",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления рецепта",
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True
    )
    short_link = models.CharField(
        "Короткая ссылка",
        max_length=NAME_LENGTH,
        blank=True,
        unique=True,
        null=True,
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = "recipes"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Промежуточная модель ингредиентов в рецепте
    """

    recipe = models.ForeignKey(
        Recipe, verbose_name="Рецепт", on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, verbose_name="Ингредиент", on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        "Количество в рецепте",
        validators=[
            MinValueValidator(MIN_AMOUNT),
        ],
    )

    class Meta:
        default_related_name = "recipe_ingredients"
        verbose_name = "Рецепт-ингредиент"
        verbose_name_plural = "Рецепты-ингредиенты"
        ordering = ("ingredient",)


class FavoriteRecipe(models.Model):
    """
    Модель любимых рецептов
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        default_related_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_favorite_recipe",
            ),
        ]


class ShoppingCart(models.Model):
    """
    Модель корзины
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        db_index=True,
    )
    recipe = models.ForeignKey(
        Recipe, verbose_name="Рецепт", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзина покупок"
        default_related_name = "shopping_carts"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_shopping_cart_recipe",
            ),
        ]
