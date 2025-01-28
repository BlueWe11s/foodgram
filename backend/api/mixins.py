from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe


class RecipeActionMixin(serializers.ModelSerializer):
    '''
    Сериализатор избранного и корзины
    '''

    class Meta:
        model = Recipe
        fields = ('id',)

    def validate(self, data):
        user = self.context['request'].user
        pk = self.context['id']
        recipe = get_object_or_404(Recipe, id=pk)

        if self.already_added(user, recipe):
            raise serializers.ValidationError(self.already_added_message)

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        pk = self.context['id']
        recipe = get_object_or_404(Recipe, id=pk)
        action_item = self._add_to_user_collection(user, recipe)
        return action_item.recipe

    def delete(self, user):
        pk = self.context['id']
        recipe = get_object_or_404(Recipe, id=pk)
        action_item = self._get_from_user_collection(user, recipe)

        if not action_item:
            raise serializers.ValidationError(self.removed_message)

        action_item.delete()
