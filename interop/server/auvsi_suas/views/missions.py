"""Missions view."""

import copy
import csv
import io
import json
import logging
import math
import numpy as np
import zipfile
from auvsi_suas.models import distance
from auvsi_suas.models import mission_evaluation
from auvsi_suas.models import units
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.uas_telemetry import UasTelemetry
from auvsi_suas.patches.simplekml_patch import AltitudeMode
from auvsi_suas.patches.simplekml_patch import Color
from auvsi_suas.patches.simplekml_patch import Kml
from auvsi_suas.patches.simplekml_patch import RefreshMode
from auvsi_suas.proto import interop_api_pb2
from auvsi_suas.views.decorators import require_login
from auvsi_suas.views.decorators import require_superuser
from auvsi_suas.views.json import ProtoJsonEncoder
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic import View
from google.protobuf import json_format

logger = logging.getLogger(__name__)

KML_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
KML_DROP_ICON = 'http://maps.google.com/mapfiles/kml/shapes/target.png'
KML_HOME_ICON = 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png'
KML_OBST_NUM_POINTS = 20
KML_ODLC_ICON = 'http://maps.google.com/mapfiles/kml/shapes/donut.png'
KML_PLANE_ICON = 'http://maps.google.com/mapfiles/kml/shapes/airports.png'
KML_WAYPOINT_ICON = 'http://maps.google.com/mapfiles/kml/paddle/blu-circle.png'


def mission_proto(mission):
    """Converts a mission to protobuf format."""
    mission_proto = interop_api_pb2.Mission()
    mission_proto.id = mission.pk

    for fly_zone in mission.fly_zones.select_related().all():
        fly_zone_proto = mission_proto.fly_zones.add()
        fly_zone_proto.altitude_min = fly_zone.altitude_msl_min
        fly_zone_proto.altitude_max = fly_zone.altitude_msl_max
        for boundary_point in fly_zone.boundary_pts.order_by(
                'order').select_related().all():
            boundary_proto = fly_zone_proto.boundary_points.add()
            boundary_proto.latitude = boundary_point.position.gps_position.latitude
            boundary_proto.longitude = boundary_point.position.gps_position.longitude

    for waypoint in mission.mission_waypoints.order_by(
            'order').select_related().all():
        waypoint_proto = mission_proto.waypoints.add()
        waypoint_proto.latitude = waypoint.position.gps_position.latitude
        waypoint_proto.longitude = waypoint.position.gps_position.longitude
        waypoint_proto.altitude = waypoint.position.altitude_msl

    for search_point in mission.search_grid_points.order_by(
            'order').select_related().all():
        search_point_proto = mission_proto.search_grid_points.add()
        search_point_proto.latitude = search_point.position.gps_position.latitude
        search_point_proto.longitude = search_point.position.gps_position.longitude

    mission_proto.off_axis_odlc_pos.latitude = mission.off_axis_odlc_pos.latitude
    mission_proto.off_axis_odlc_pos.longitude = mission.off_axis_odlc_pos.longitude

    mission_proto.emergent_last_known_pos.latitude = mission.emergent_last_known_pos.latitude
    mission_proto.emergent_last_known_pos.longitude = mission.emergent_last_known_pos.longitude

    mission_proto.air_drop_pos.latitude = mission.air_drop_pos.latitude
    mission_proto.air_drop_pos.longitude = mission.air_drop_pos.longitude

    stationary_obstacles = mission.stationary_obstacles.select_related().all(
    ).order_by('pk')
    for obst in stationary_obstacles:
        obst_proto = mission_proto.stationary_obstacles.add()
        obst_proto.latitude = obst.gps_position.latitude
        obst_proto.longitude = obst.gps_position.longitude
        obst_proto.radius = obst.cylinder_radius
        obst_proto.height = obst.cylinder_height

    return mission_proto


class Missions(View):
    """Handles requests for all missions for admins."""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(Missions, self).dispatch(*args, **kwargs)

    def get(self, request):
        missions = MissionConfig.objects.all()
        out = []
        for mission in missions:
            out.append(mission_proto(mission))

        return HttpResponse(
            json.dumps(out, cls=ProtoJsonEncoder),
            content_type="application/json")


class MissionsId(View):
    """Handles requests for a specific mission."""

    @method_decorator(require_login)
    def dispatch(self, *args, **kwargs):
        return super(MissionsId, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        try:
            mission = MissionConfig.objects.get(pk=pk)
        except MissionConfig.DoesNotExist:
            return HttpResponseNotFound('Mission %s not found.' % pk)

        return HttpResponse(
            json_format.MessageToJson(mission_proto(mission)),
            content_type="application/json")


def fly_zone_kml(fly_zone, kml):
    """
    Appends kml nodes describing the flyzone.

    Args:
        fly_zone: The FlyZone for which to add KML
        kml: A simpleKML Container to which the fly zone will be added
    """

    zone_name = 'Fly Zone {}'.format(fly_zone.pk)
    pol = kml.newpolygon(name=zone_name)
    fly_zone_points = []
    for point in fly_zone.boundary_pts.order_by('order'):
        gps = point.position.gps_position
        coord = (gps.longitude, gps.latitude,
                 units.feet_to_meters(point.position.altitude_msl))
        fly_zone_points.append(coord)
    fly_zone_points.append(fly_zone_points[0])
    pol.outerboundaryis = fly_zone_points
    pol.style.linestyle.color = Color.red
    pol.style.linestyle.width = 3
    pol.style.polystyle.color = Color.changealphaint(50, Color.green)


def mission_kml(mission, kml, kml_doc):
    """
    Appends kml nodes describing the mission.

    Args:
        mission: The mission to add to the KML.
        kml: A simpleKML Container to which the mission data will be added
        kml_doc: The simpleKML Document to which schemas will be added

    Returns:
        The KML folder for the mission data.
    """
    mission_name = 'Mission {}'.format(mission.pk)
    kml_folder = kml.newfolder(name=mission_name)

    # Flight boundaries.
    fly_zone_folder = kml_folder.newfolder(name='Fly Zones')
    for flyzone in mission.fly_zones.all():
        fly_zone_kml(flyzone, fly_zone_folder)

    # Static points.
    locations = [
        ('Home', mission.home_pos, KML_HOME_ICON),
        ('Emergent LKP', mission.emergent_last_known_pos, KML_ODLC_ICON),
        ('Off Axis', mission.off_axis_odlc_pos, KML_ODLC_ICON),
        ('Air Drop', mission.air_drop_pos, KML_DROP_ICON),
    ]
    for key, point, icon in locations:
        gps = (point.longitude, point.latitude)
        p = kml_folder.newpoint(name=key, coords=[gps])
        p.iconstyle.icon.href = icon
        p.description = str(point)

    # ODLCs.
    oldc_folder = kml_folder.newfolder(name='ODLCs')
    for odlc in mission.odlcs.all():
        name = 'ODLC %d' % odlc.pk
        gps = (odlc.location.longitude, odlc.location.latitude)
        p = oldc_folder.newpoint(name=name, coords=[gps])
        p.iconstyle.icon.href = KML_ODLC_ICON
        p.description = name

    # Waypoints
    waypoints_folder = kml_folder.newfolder(name='Waypoints')
    linestring = waypoints_folder.newlinestring(name='Waypoints')
    waypoints = []
    for i, waypoint in enumerate(mission.mission_waypoints.order_by('order')):
        gps = waypoint.position.gps_position
        coord = (gps.longitude, gps.latitude,
                 units.feet_to_meters(waypoint.position.altitude_msl))
        waypoints.append(coord)

        # Add waypoint marker
        p = waypoints_folder.newpoint(
            name='Waypoint %d' % (i + 1), coords=[coord])
        p.iconstyle.icon.href = KML_WAYPOINT_ICON
        p.description = str(waypoint)
        p.altitudemode = AltitudeMode.absolute
        p.extrude = 1
    linestring.coords = waypoints
    linestring.altitudemode = AltitudeMode.absolute
    linestring.extrude = 1
    linestring.style.linestyle.color = Color.green
    linestring.style.polystyle.color = Color.changealphaint(100, Color.green)

    # Search Area
    search_area = []
    for point in mission.search_grid_points.order_by('order'):
        gps = point.position.gps_position
        coord = (gps.longitude, gps.latitude,
                 units.feet_to_meters(point.position.altitude_msl))
        search_area.append(coord)
    if search_area:
        search_area.append(search_area[0])
        pol = kml_folder.newpolygon(name='Search Area')
        pol.outerboundaryis = search_area
        pol.style.linestyle.color = Color.blue
        pol.style.linestyle.width = 2
        pol.style.polystyle.color = Color.changealphaint(50, Color.blue)

    # Stationary Obstacles.
    stationary_obstacles_folder = kml_folder.newfolder(
        name='Stationary Obstacles')
    for obst in mission.stationary_obstacles.all():
        gpos = obst.gps_position
        zone, north = distance.utm_zone(gpos.latitude, gpos.longitude)
        proj = distance.proj_utm(zone, north)
        cx, cy = proj(gpos.longitude, gpos.latitude)
        rm = units.feet_to_meters(obst.cylinder_radius)
        hm = units.feet_to_meters(obst.cylinder_height)
        obst_points = []
        for angle in np.linspace(0, 2 * math.pi, num=KML_OBST_NUM_POINTS):
            px = cx + rm * math.cos(angle)
            py = cy + rm * math.sin(angle)
            lon, lat = proj(px, py, inverse=True)
            obst_points.append((lon, lat, hm))
        pol = stationary_obstacles_folder.newpolygon(
            name='Obstacle %d' % obst.pk)
        pol.outerboundaryis = obst_points
        pol.altitudemode = AltitudeMode.absolute
        pol.extrude = 1
        pol.style.linestyle.color = Color.yellow
        pol.style.linestyle.width = 2
        pol.style.polystyle.color = Color.changealphaint(50, Color.yellow)

    return kml_folder


def uas_telemetry_kml(user, flights, logs, kml, kml_doc):
    """
    Appends kml nodes describing the given user's flight as described
    by the log array given.

    Args:
        user: A Django User to get username from
        flights: List of flight periods
        logs: A list of UasTelemetry elements
        kml: A simpleKML Container to which the flight data will be added
        kml_doc: The simpleKML Document to which schemas will be added
    Returns:
        None
    """
    kml_folder = kml.newfolder(name=user.username)

    logs = UasTelemetry.dedupe(UasTelemetry.filter_bad(logs))
    for i, flight in enumerate(flights):
        name = '%s Flight %d' % (user.username, i + 1)
        flight_logs = filter(lambda x: flight.within(x.timestamp), logs)

        coords = []
        angles = []
        when = []
        for entry in logs:
            pos = entry.uas_position.gps_position
            # Spatial Coordinates
            coord = (pos.longitude, pos.latitude,
                     units.feet_to_meters(entry.uas_position.altitude_msl))
            coords.append(coord)

            # Time Elements
            time = entry.timestamp.strftime(KML_DATETIME_FORMAT)
            when.append(time)

            # Degrees heading, tilt, and roll
            angle = (entry.uas_heading, 0.0, 0.0)
            angles.append(angle)

        # Create a new track in the folder
        trk = kml_folder.newgxtrack(name=name)
        trk.altitudemode = AltitudeMode.absolute

        # Append flight data
        trk.newwhen(when)
        trk.newgxcoord(coords)
        trk.newgxangle(angles)

        # Set styling
        trk.extrude = 1  # Extend path to ground
        trk.style.linestyle.width = 2
        trk.style.linestyle.color = Color.blue
        trk.iconstyle.icon.href = KML_PLANE_ICON


def uas_telemetry_live_kml(kml, timespan):
    users = User.objects.all().order_by('username')
    for user in users:
        try:
            log = UasTelemetry.by_user(user).latest('timestamp')
        except UasTelemetry.DoesNotExist:
            continue

        if log.timestamp < timezone.now() - timespan:
            continue

        apos = log.uas_position
        gpos = apos.gps_position

        point = kml.newpoint(
            name=user.username,
            coords=[(gpos.longitude, gpos.latitude,
                     units.feet_to_meters(apos.altitude_msl))])
        point.iconstyle.icon.href = KML_PLANE_ICON
        point.iconstyle.heading = log.uas_heading
        point.extrude = 1  # Extend path to ground
        point.altitudemode = AltitudeMode.absolute


class ExportKml(View):
    """ Generates a KML file HttpResponse"""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(ExportKml, self).dispatch(*args, **kwargs)

    def get(self, request):
        kml = Kml(name='AUVSI SUAS Flight Data')
        kml_missions = kml.newfolder(name='Missions')
        users = User.objects.all()
        for mission in MissionConfig.objects.all():
            kml_mission = mission_kml(mission, kml_missions, kml.document)
            kml_flights = kml_mission.newfolder(name='Flights')
            for user in users:
                if user.is_superuser:
                    continue
                flights = TakeoffOrLandingEvent.flights(mission, user)
                if not flights:
                    continue
                uas_telemetry_kml(
                    user=user,
                    flights=flights,
                    logs=UasTelemetry.by_user(user),
                    kml=kml_flights,
                    kml_doc=kml.document)

        response = HttpResponse(kml.kml())
        response['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        response['Content-Disposition'] = 'attachment; filename=mission.kml'
        response['Content-Length'] = str(len(response.content))
        return response


class LiveKml(View):
    """ Generates a KML for live display.
    This KML uses a network link to update via the update.kml endpoint
    """

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(LiveKml, self).dispatch(*args, **kwargs)

    def get(self, request):
        kml = Kml(name='AUVSI SUAS LIVE Flight Data')
        kml_missions = kml.newfolder(name='Missions')
        for mission in MissionConfig.objects.all():
            mission_kml(mission, kml_missions, kml.document)

        parameters = '?sessionid={}'.format(request.COOKIES['sessionid'])
        uri = request.build_absolute_uri(
            '/api/missions/update.kml') + parameters

        netlink = kml.newnetworklink(name="Live Data")
        netlink.link.href = uri
        netlink.link.refreshmode = RefreshMode.oninterval
        netlink.link.refreshinterval = 1.0

        response = HttpResponse(kml.kml())
        response['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        response['Content-Disposition'] = 'attachment; filename=live.kml'
        response['Content-Length'] = str(len(response.content))
        return response


def set_request_session_from_cookie(func):
    def wrapper(request):
        if 'sessionid' not in request.GET:
            # No session ID, attempt to use cookies.
            return func(request)

        try:
            # Pack the params back into the cookie
            request.COOKIES['sessionid'] = request.GET['sessionid']

            # Update the user associated with the cookie
            session = Session.objects.get(session_key=request.GET['sessionid'])
            uid = session.get_decoded().get('_auth_user_id')
            request.user = User.objects.get(pk=uid)
        except ObjectDoesNotExist:
            return HttpResponseForbidden()
        else:
            return func(request)

    return wrapper


class LiveKmlUpdate(View):
    """Generates the live update portion of LiveKml"""

    @method_decorator(set_request_session_from_cookie)
    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(LiveKmlUpdate, self).dispatch(*args, **kwargs)

    def get(self, request):
        kml = Kml(name='LIVE Data')
        uas_telemetry_live_kml(kml, timedelta(seconds=5))

        response = HttpResponse(kml.kml())
        response['Content-Type'] = 'application/vnd.google-earth.kml+xml'
        response['Content-Disposition'] = 'attachment; filename=update.kml'
        response['Content-Length'] = str(len(response.content))
        return response


def pretty_json(json_str):
    """Generates a pretty-print json from any json."""
    return json.dumps(json.loads(json_str), indent=4)


class Evaluate(View):
    """Evaluates the teams and returns a zip file with CSV & JSON data.

    Zip file contains a master CSV and JSON file with all evaluation data.
    It also contains per-team JSON files for individual team feedback.
    """

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(Evaluate, self).dispatch(*args, **kwargs)

    def csv_from_json(self, json_list):
        """Generates a CSV string from a list of rows as JSON strings."""
        csv_list = []
        for json_row in json_list:
            csv_dict = {}
            work_queue = [([], json.loads(json_row))]
            while len(work_queue) > 0:
                (cur_prefixes, cur_val) = work_queue.pop()
                if isinstance(cur_val, dict):
                    for (key, val) in cur_val.items():
                        new_prefixes = copy.copy(cur_prefixes)
                        new_prefixes.append(str(key))
                        work_queue.append((new_prefixes, val))
                elif isinstance(cur_val, list):
                    for ix, val in enumerate(cur_val):
                        new_prefixes = copy.copy(cur_prefixes)
                        new_prefixes.append(str(ix))
                        work_queue.append((new_prefixes, val))
                else:
                    column_key = '.'.join(cur_prefixes)
                    csv_dict[column_key] = cur_val
            csv_list.append(csv_dict)

        col_headers = set()
        for csv_dict in csv_list:
            col_headers.update(csv_dict.keys())
        col_headers = sorted(col_headers)

        csv_io = io.StringIO()
        writer = csv.DictWriter(csv_io, fieldnames=col_headers)
        writer.writeheader()
        for csv_dict in csv_list:
            writer.writerow(csv_dict)
        csv_output = csv_io.getvalue()
        csv_io.close()

        return csv_output

    def get(self, request, pk):
        try:
            mission = MissionConfig.objects.select_related().get(pk=pk)
        except MissionConfig.DoesNotExist:
            return HttpResponseBadRequest('Mission not found.')

        # Get the optional team to eval.
        users = None
        if 'team' in request.GET:
            try:
                team = int(request.GET['team'])
                users = [User.objects.get(pk=team)]
            except TypeError:
                return HttpResponseBadRequest('Team not an ID.')
            except User.DoesNotExist:
                return HttpResponseNotFound('Team not found.')

        # Get the eval data for the teams.
        mission_eval = mission_evaluation.evaluate_teams(mission, users)
        if not mission_eval:
            return HttpResponseServerError(
                'Could not get user evaluation data.')

        # Form Zip file.
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zip_file:
            zip_file.writestr(
                '/evaluate_teams/all.json',
                pretty_json(json_format.MessageToJson(mission_eval)))
            team_jsons = []
            for team_eval in mission_eval.teams:
                team_json = pretty_json(json_format.MessageToJson(team_eval))
                zip_file.writestr(
                    '/evaluate_teams/teams/%s.json' % team_eval.team,
                    team_json)
                team_jsons.append(team_json)

            zip_file.writestr('/evaluate_teams/all.csv',
                              self.csv_from_json(team_jsons))
        zip_output = zip_io.getvalue()
        zip_io.close()

        return HttpResponse(zip_output, content_type='application/zip')


class MissionDetails(TemplateView):
    """Renders the mission details as a printable webpage."""

    template_name = 'mission.html'

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(MissionDetails, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MissionDetails, self).get_context_data(**kwargs)
        pk = int(kwargs['pk'])
        proto = mission_proto(MissionConfig.objects.get(pk=pk))
        context['mission'] = proto
        context['mission_str'] = pretty_json(json_format.MessageToJson(proto))
        return context
