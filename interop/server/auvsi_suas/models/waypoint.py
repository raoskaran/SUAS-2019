"""Waypoint model."""

import logging
from auvsi_suas.models.aerial_position import AerialPosition
from django.contrib import admin
from django.db import models

logger = logging.getLogger(__name__)


class Waypoint(models.Model):
    """A waypoint consists of an aerial position and its order in a set."""

    # Aerial position.
    position = models.ForeignKey(AerialPosition, on_delete=models.CASCADE)
    # Waypoint relative order number. Should be unique per waypoint set.
    order = models.IntegerField(db_index=True)

    def distance_to(self, other):
        """Computes distance to another waypoint.
        Args:
          other: The other waypoint.
        Returns:
          Distance in feet.
        """
        return self.position.distance_to(other.position)


@admin.register(Waypoint)
class WaypointModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    raw_id_fields = ("position", )
    list_display = ('pk', 'position', 'order')
