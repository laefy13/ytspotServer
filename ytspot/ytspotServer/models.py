from django.db import models
from django import forms
from djongo import models as mongoModels
from django.core.validators import RegexValidator


# Create your models here.
class SpotifyUser(models.Model):
    uuid = models.CharField(
        max_length=36,
        validators=[
            RegexValidator(
                regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
                message="Enter a valid UUID.",
                code="invalid_uuid",
            )
        ],
    )
    refresh_token = models.CharField(max_length=100)
    token = models.CharField(max_length=100)
    browser_id = models.CharField(max_length=255)
    added_at = models.DateTimeField(auto_now_add=True)


class PlaylistItems(mongoModels.Model):
    item = mongoModels.CharField(max_length=255)

    class Meta:
        abstract = True


class PlaylistsQueries(mongoModels.Model):
    playlist_id = mongoModels.CharField(max_length=255)
    playlist_time = mongoModels.IntegerField(default=0)
    playlist_items = mongoModels.JSONField()
