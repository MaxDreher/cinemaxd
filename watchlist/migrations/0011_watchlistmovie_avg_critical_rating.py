# Generated by Django 5.0 on 2024-01-24 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watchlist', '0010_movie_avg_critical_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='watchlistmovie',
            name='avg_critical_rating',
            field=models.FloatField(null=True),
        ),
    ]