# Generated by Django 3.2 on 2025-02-09 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_users_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='avatar',
            field=models.CharField(blank=True, max_length=254),
        ),
    ]
