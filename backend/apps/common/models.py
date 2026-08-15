"""Building blocks shared by every domain model."""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """UUID primary key plus creation and update stamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
