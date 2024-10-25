# Generated by Django 5.1.2 on 2024-10-25 03:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wishlist', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wishlistitem',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='wishlistitem',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]