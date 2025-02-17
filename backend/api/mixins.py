from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe


class RecipeActionMixin(serializers.ModelSerializer):
    '''
    Миксин использующийся в сериализаторе избранного и корзины
    '''

    class Meta:
        model = Recipe
        fields = ('id',)

    def validate(self, data):
        user = self.context['request'].user
        id = self.context['id']
        recipe = get_object_or_404(Recipe, id=id)
        if recipe.favorites.filter(user=user).exists():
            raise serializers.ValidationError(self.added_message)
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        id = self.context['id']
        recipe = get_object_or_404(Recipe, id=id)
        action_item = user.favorites.create(recipe=recipe)
        return action_item.recipe

    def delete(self, user):
        id = self.context['id']
        recipe = get_object_or_404(Recipe, id=id)
        action_item = user.favorites.filter(recipe=recipe).first()
        if not action_item:
            raise serializers.ValidationError(self.removed_message)

        action_item.delete()
