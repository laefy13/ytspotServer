from django.db import models
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
    token = models.CharField(max_length=100)
    added_at = models.DateTimeField(auto_now_add=True)
