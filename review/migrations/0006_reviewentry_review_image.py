# Generated by Django 5.1.2 on 2024-10-24 02:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0005_remove_reviewentry_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewentry',
            name='review_image',
            field=models.ImageField(blank=True, null=True, upload_to='reviews/'),
        ),
    ]
