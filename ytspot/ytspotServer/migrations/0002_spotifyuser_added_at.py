# Generated by Django 4.2.11 on 2024-04-16 14:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ytspotServer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='spotifyuser',
            name='added_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
