import json

from django.contrib.auth import get_user_model

from backend.recipes.models import Ingredient, Tags


User = get_user_model()


with open('ingredients.json', 'r', encoding='utf-8') as ingredients_file:
    ingredients_json = json.load(ingredients_file)

with open('tags.json', 'r', encoding='utf-8') as tags_file:
    tags_json = json.load(tags_file)

ingredients = [Ingredient(
    name=item['name'], measurement_unit=item['measurement_unit']
) for item in ingredients_json]

tags = [Tags(
    name=item['name'], slug=item['slug']
) for item in tags_json]

Ingredient.objects.bulk_create(ingredients)
Tags.objects.bulk_create(tags)
admin = User.objects.create(username='admin', email='admin@a.ru',
                            is_staff=True, is_superuser=True)
admin.set_password('admin')
admin.save()
