from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_config import MissionConfig

# Print all mission objects.
print MissionConfig.objects.all()

# Create and save a GPS position.
gpos = GpsPosition(latitudel=38.145335, longitude=-76.427512)
gpos.save()