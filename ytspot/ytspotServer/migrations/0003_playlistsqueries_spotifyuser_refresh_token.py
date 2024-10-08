# Generated by Django 4.1.13 on 2024-09-24 11:31

from django.db import migrations, models
import django.utils.timezone
import djongo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ytspotServer', '0002_spotifyuser_added_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlaylistsQueries',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlist_id', models.CharField(max_length=255)),
                ('playlist_items', djongo.models.fields.JSONField()),
            ],
        ),
        migrations.AddField(
            model_name='spotifyuser',
            name='refresh_token',
            field=models.CharField(default=django.utils.timezone.now, max_length=100),
            preserve_default=False,
        ),
    ]
