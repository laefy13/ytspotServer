# Generated by Django 4.1.13 on 2024-10-05 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ytspotServer', '0004_spotifyuser_browser_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlistsqueries',
            name='playlist_time',
            field=models.IntegerField(default=0, max_length=1),
        ),
    ]
