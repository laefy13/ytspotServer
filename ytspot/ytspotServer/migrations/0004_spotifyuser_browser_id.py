# Generated by Django 4.1.13 on 2024-09-27 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ytspotServer', '0003_playlistsqueries_spotifyuser_refresh_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='spotifyuser',
            name='browser_id',
            field=models.CharField(default='1231c23', max_length=255),
            preserve_default=False,
        ),
    ]
