# Generated by Django 3.2 on 2025-02-28 06:44

from django.conf import settings
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import user.validator


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='users',
            name='username',
            field=models.CharField(max_length=50, unique=True, validators=[user.validator.validate_username, django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='Логин'),
        ),
    ]
