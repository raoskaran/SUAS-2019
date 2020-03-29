"""Tests for the mission_evaluation module."""

from django.contrib.auth.models import User
from django.test import TestCase

from auvsi_suas.models import mission_evaluation
from auvsi_suas.models import mission_config
from auvsi_suas.proto import interop_admin_api_pb2


class TestMissionScoring(TestCase):
    """Tests the score conversion for the mission_evaluation module."""

    def setUp(self):
        """Create a base evaluation to save redefining it."""
        self.eval = interop_admin_api_pb2.MissionEvaluation()
        self.eval.team.username = 'team'
        feedback = self.eval.feedback
        feedback.uas_telemetry_time_max_sec = 1.0
        feedback.uas_telemetry_time_avg_sec = 1.0
        wpt = feedback.waypoints.add()
        wpt.score_ratio = 0.5
        wpt = feedback.waypoints.add()
        wpt.score_ratio = 0.2
        obs = feedback.stationary_obstacles.add()
        obs.hit = True
        obs = feedback.stationary_obstacles.add()
        obs.hit = False
        odlcs = feedback.odlc
        odlcs.score_ratio = 0.46
        odlcs.extra_object_penalty_ratio = 0.1
        t = odlcs.odlcs.add()
        t.score_ratio = 0.96
        t.classifications_score_ratio = 0.6
        t.geolocation_score_ratio = 0.2
        t.actionable_score_ratio = 1.0
        t.autonomous_score_ratio = 1.0
        t = odlcs.odlcs.add()
        t.score_ratio = 0.16
        t.classifications_score_ratio = 0.2
        t.geolocation_score_ratio = 0.6
        t.actionable_score_ratio = 0.0
        t.autonomous_score_ratio = 0.0
        judge = feedback.judge
        judge.flight_time_sec = 60 * 6
        judge.post_process_time_sec = 60 * 4
        judge.used_timeout = True
        judge.min_auto_flight_time = True
        judge.safety_pilot_takeovers = 2
        judge.waypoints_captured = 2
        judge.out_of_bounds = 2
        judge.unsafe_out_of_bounds = 1
        judge.things_fell_off_uas = False
        judge.crashed = False
        judge.air_drop_accuracy = interop_admin_api_pb2.MissionJudgeFeedback.WITHIN_75_FT
        judge.ugv_drove_to_location = False
        judge.operational_excellence_percent = 90

    def test_timeline(self):
        """Test the timeline scoring."""
        judge = self.eval.feedback.judge
        timeline = self.eval.score.timeline

        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.93333333, timeline.mission_time)
        self.assertAlmostEqual(0, timeline.mission_penalty)
        self.assertAlmostEqual(0, timeline.timeout)
        self.assertAlmostEqual(0.74666666666, timeline.score_ratio)

        judge.flight_time_sec = 60 * 20
        judge.post_process_time_sec = 0
        judge.used_timeout = False
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(1, timeline.mission_time)
        self.assertAlmostEqual(0, timeline.mission_penalty)
        self.assertAlmostEqual(1, timeline.timeout)
        self.assertAlmostEqual(1, timeline.score_ratio)

        judge.flight_time_sec = 60 * 25
        judge.post_process_time_sec = 60 * 5
        judge.used_timeout = True
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.5, timeline.mission_time)
        self.assertAlmostEqual(0, timeline.mission_penalty)
        self.assertAlmostEqual(0, timeline.timeout)
        self.assertAlmostEqual(0.4, timeline.score_ratio)

        judge.flight_time_sec = 60 * 30
        judge.post_process_time_sec = 60 * 10
        judge.used_timeout = True
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0, timeline.mission_time)
        self.assertAlmostEqual(0, timeline.mission_penalty)
        self.assertAlmostEqual(0, timeline.timeout)
        self.assertAlmostEqual(0, timeline.score_ratio)

        judge.flight_time_sec = 60 * 35
        judge.post_process_time_sec = 60 * 20
        judge.used_timeout = True
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0, timeline.mission_time)
        self.assertAlmostEqual(27, timeline.mission_penalty)
        self.assertAlmostEqual(0, timeline.timeout)
        self.assertAlmostEqual(-27, timeline.score_ratio)

    def test_autonomous_flight(self):
        """Test the autonomous flight scoring."""
        feedback = self.eval.feedback
        judge = feedback.judge
        flight = self.eval.score.autonomous_flight

        mission_evaluation.score_team(self.eval)
        self.assertTrue(flight.telemetry_prerequisite)
        self.assertAlmostEqual(1, flight.flight)
        self.assertAlmostEqual(1, flight.waypoint_capture)
        self.assertAlmostEqual(0.35, flight.waypoint_accuracy)
        self.assertAlmostEqual(0.2, flight.safety_pilot_takeover_penalty)
        self.assertAlmostEqual(1.2, flight.out_of_bounds_penalty)
        self.assertEqual(0, flight.things_fell_off_penalty)
        self.assertEqual(0, flight.crashed_penalty)
        self.assertAlmostEqual(-0.725, flight.score_ratio)

        feedback.waypoints[1].score_ratio = 1
        judge.waypoints_captured = 1
        judge.safety_pilot_takeovers = 0
        judge.out_of_bounds = 0
        judge.unsafe_out_of_bounds = 0
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(1, flight.flight)
        self.assertAlmostEqual(0.5, flight.waypoint_capture)
        self.assertAlmostEqual(0.75, flight.waypoint_accuracy)
        self.assertAlmostEqual(0, flight.safety_pilot_takeover_penalty)
        self.assertAlmostEqual(0, flight.out_of_bounds_penalty)
        self.assertAlmostEqual(0.825, flight.score_ratio)

        judge.things_fell_off_uas = True
        judge.crashed = True
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.25, flight.things_fell_off_penalty)
        self.assertAlmostEqual(0.35, flight.crashed_penalty)
        self.assertAlmostEqual(0.225, flight.score_ratio)

        judge.min_auto_flight_time = False
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0, flight.flight)
        judge.flight_time_sec = 0
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0, flight.flight)
        self.assertAlmostEqual(0, self.eval.score.score_ratio)

        feedback.uas_telemetry_time_avg_sec = 2.0
        mission_evaluation.score_team(self.eval)
        self.assertFalse(flight.telemetry_prerequisite)
        self.assertAlmostEqual(0, flight.waypoint_accuracy)

    def test_obstacles(self):
        """Test the obstacle scoring."""
        feedback = self.eval.feedback
        avoid = self.eval.score.obstacle_avoidance

        mission_evaluation.score_team(self.eval)
        self.assertTrue(avoid.telemetry_prerequisite)
        self.assertAlmostEqual(0.125, avoid.score_ratio)

        feedback.stationary_obstacles[0].hit = False
        mission_evaluation.score_team(self.eval)
        self.assertTrue(avoid.telemetry_prerequisite)
        self.assertAlmostEqual(1, avoid.score_ratio)

        feedback.uas_telemetry_time_avg_sec = 1.01
        mission_evaluation.score_team(self.eval)
        self.assertFalse(avoid.telemetry_prerequisite)
        self.assertAlmostEqual(0, avoid.score_ratio)

    def test_objects(self):
        """Test the object scoring."""
        feedback = self.eval.feedback
        objects = self.eval.score.object

        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.4, objects.characteristics)
        self.assertAlmostEqual(0.4, objects.geolocation)
        self.assertAlmostEqual(0.5, objects.actionable)
        self.assertAlmostEqual(0.5, objects.autonomy)
        self.assertAlmostEqual(0.1, objects.extra_object_penalty)
        self.assertAlmostEqual(0.46, objects.score_ratio)

        del feedback.odlc.odlcs[:]
        feedback.odlc.extra_object_penalty_ratio = 0
        feedback.odlc.score_ratio = 0
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0, objects.characteristics)
        self.assertAlmostEqual(0, objects.geolocation)
        self.assertAlmostEqual(0, objects.actionable)
        self.assertAlmostEqual(0, objects.autonomy)
        self.assertAlmostEqual(0, objects.extra_object_penalty)
        self.assertAlmostEqual(0, objects.score_ratio)

    def test_air_drop(self):
        """Test the air drop scoring."""
        judge = self.eval.feedback.judge
        air = self.eval.score.air_drop

        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.25, air.drop_accuracy)
        self.assertAlmostEqual(0, air.drive_to_location)
        self.assertAlmostEqual(0.125, air.score_ratio)

        judge.air_drop_accuracy = interop_admin_api_pb2.MissionJudgeFeedback.WITHIN_05_FT
        judge.ugv_drove_to_location = True
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(1, air.drop_accuracy)
        self.assertAlmostEqual(1, air.drive_to_location)
        self.assertAlmostEqual(1, air.score_ratio)

        judge.air_drop_accuracy = interop_admin_api_pb2.MissionJudgeFeedback.WITHIN_25_FT
        judge.ugv_drove_to_location = True
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.5, air.drop_accuracy)
        self.assertAlmostEqual(1, air.drive_to_location)
        self.assertAlmostEqual(0.75, air.score_ratio)

    def test_operational(self):
        """Test the operational excellence scoring."""
        operational = self.eval.score.operational_excellence

        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.9, operational.score_ratio)

    def test_total(self):
        """Test the total scoring."""
        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0.1616666666666667, self.eval.score.score_ratio)

    def test_non_negative(self):
        """Test that total score doesn't go negative."""
        self.eval = interop_admin_api_pb2.MissionEvaluation()
        self.eval.team.username = 'team'
        feedback = self.eval.feedback
        feedback.uas_telemetry_time_max_sec = 100.0
        feedback.uas_telemetry_time_avg_sec = 100.0
        wpt = feedback.waypoints.add()
        wpt.score_ratio = 0
        wpt = feedback.waypoints.add()
        wpt.score_ratio = 0
        obs = feedback.stationary_obstacles.add()
        obs.hit = True
        obs = feedback.stationary_obstacles.add()
        obs.hit = True
        odlcs = feedback.odlc
        odlcs.score_ratio = 0
        odlcs.extra_object_penalty_ratio = 1.0
        t = odlcs.odlcs.add()
        t.score_ratio = 0
        t.classifications_score_ratio = 0
        t.geolocation_score_ratio = 0
        t.actionable_score_ratio = 0
        t.autonomous_score_ratio = 0
        judge = feedback.judge
        judge.flight_time_sec = 60 * 100
        judge.post_process_time_sec = 60 * 100
        judge.used_timeout = True
        judge.min_auto_flight_time = True
        judge.safety_pilot_takeovers = 10
        judge.waypoints_captured = 0
        judge.out_of_bounds = 10
        judge.unsafe_out_of_bounds = 5
        judge.things_fell_off_uas = True
        judge.crashed = False
        judge.air_drop_accuracy = interop_admin_api_pb2.MissionJudgeFeedback.INSUFFICIENT_ACCURACY
        judge.ugv_drove_to_location = False
        judge.operational_excellence_percent = 0

        mission_evaluation.score_team(self.eval)
        self.assertAlmostEqual(0, self.eval.score.score_ratio)


class TestMissionEvaluation(TestCase):
    """Tests the mission_evaluation module."""
    fixtures = ['testdata/sample_mission.json']

    def test_evaluate_teams(self):
        """Tests the evaluation of teams method."""
        user0 = User.objects.get(username='user0')
        user1 = User.objects.get(username='user1')
        config = mission_config.MissionConfig.objects.get(pk=3)

        mission_eval = mission_evaluation.evaluate_teams(config)

        # Contains user0 and user1
        self.assertEqual(2, len(mission_eval.teams))

        # user0 data
        user_eval = mission_eval.teams[0]
        self.assertEqual(user0.username, user_eval.team.username)
        self.assertEqual(user0.first_name, user_eval.team.name)
        self.assertEqual(user0.last_name, user_eval.team.university)
        feedback = user_eval.feedback
        score = user_eval.score
        self.assertEqual(0.0,
                         feedback.waypoints[0].closest_for_scored_approach_ft)
        self.assertEqual(1.0, feedback.waypoints[0].score_ratio)
        self.assertEqual(0.0,
                         feedback.waypoints[1].closest_for_scored_approach_ft)

        self.assertAlmostEqual(0.5, feedback.uas_telemetry_time_max_sec)
        self.assertAlmostEqual(1. / 6, feedback.uas_telemetry_time_avg_sec)

        self.assertAlmostEqual(0.454, feedback.odlc.score_ratio, places=3)

        self.assertEqual(25, feedback.stationary_obstacles[0].id)
        self.assertEqual(True, feedback.stationary_obstacles[0].hit)
        self.assertEqual(26, feedback.stationary_obstacles[1].id)
        self.assertEqual(False, feedback.stationary_obstacles[1].hit)

        self.assertEqual(1, feedback.judge.flight_time_sec)

        self.assertAlmostEqual(0.99944444, score.timeline.mission_time)
        self.assertAlmostEqual(0, score.timeline.mission_penalty)
        self.assertAlmostEqual(1, score.timeline.timeout)
        self.assertAlmostEqual(0.99955555, score.timeline.score_ratio)
        self.assertAlmostEqual(1, score.autonomous_flight.flight)
        self.assertAlmostEqual(1, score.autonomous_flight.waypoint_capture)
        self.assertAlmostEqual(0.5, score.autonomous_flight.waypoint_accuracy)
        self.assertAlmostEqual(1.2,
                               score.autonomous_flight.out_of_bounds_penalty)
        self.assertAlmostEqual(0,
                               score.autonomous_flight.things_fell_off_penalty)
        self.assertAlmostEqual(0, score.autonomous_flight.crashed_penalty)
        self.assertAlmostEqual(-0.45, score.autonomous_flight.score_ratio)

        self.assertAlmostEqual(0.8, score.object.characteristics)
        self.assertAlmostEqual(0.423458165692, score.object.geolocation)
        self.assertAlmostEqual(0.333333333333, score.object.actionable)
        self.assertAlmostEqual(0.333333333333, score.object.autonomy)
        self.assertAlmostEqual(0, score.object.extra_object_penalty)
        self.assertAlmostEqual(0.4537041163742234, score.object.score_ratio)

        self.assertAlmostEqual(0, score.air_drop.drop_accuracy)
        self.assertAlmostEqual(0, score.air_drop.drive_to_location)
        self.assertAlmostEqual(0, score.air_drop.score_ratio)

        self.assertAlmostEqual(0.8, score.operational_excellence.score_ratio)

        self.assertAlmostEqual(0.20569637883040026, score.score_ratio)

        # user1 data
        user_eval = mission_eval.teams[1]
        self.assertEqual(user1.username, user_eval.team.username)
        self.assertEqual(user1.first_name, user_eval.team.name)
        self.assertEqual(user1.last_name, user_eval.team.university)
        feedback = user_eval.feedback
        score = user_eval.score
        self.assertEqual(0.0,
                         feedback.waypoints[0].closest_for_scored_approach_ft)
        self.assertEqual(1.0, feedback.waypoints[0].score_ratio)
        self.assertEqual(0.0,
                         feedback.waypoints[1].closest_for_scored_approach_ft)

        self.assertAlmostEqual(2.0, feedback.uas_telemetry_time_max_sec)
        self.assertAlmostEqual(1.0, feedback.uas_telemetry_time_avg_sec)

        self.assertAlmostEqual(0, feedback.odlc.score_ratio, places=3)

        self.assertEqual(25, feedback.stationary_obstacles[0].id)
        self.assertEqual(False, feedback.stationary_obstacles[0].hit)
        self.assertEqual(26, feedback.stationary_obstacles[1].id)
        self.assertEqual(False, feedback.stationary_obstacles[1].hit)

        self.assertEqual(2, feedback.judge.flight_time_sec)

        self.assertAlmostEqual(0.9997222222222222, score.timeline.mission_time)
        self.assertAlmostEqual(0, score.timeline.mission_penalty)
        self.assertAlmostEqual(0, score.timeline.timeout)
        self.assertAlmostEqual(0.7997777777777778, score.timeline.score_ratio)
        self.assertAlmostEqual(1, score.autonomous_flight.flight)
        self.assertAlmostEqual(0.5, score.autonomous_flight.waypoint_capture)
        self.assertAlmostEqual(1, score.autonomous_flight.waypoint_accuracy)
        self.assertAlmostEqual(
            0.1, score.autonomous_flight.safety_pilot_takeover_penalty)
        self.assertAlmostEqual(0,
                               score.autonomous_flight.out_of_bounds_penalty)
        self.assertAlmostEqual(0.25,
                               score.autonomous_flight.things_fell_off_penalty)
        self.assertAlmostEqual(0.35, score.autonomous_flight.crashed_penalty)
        self.assertAlmostEqual(0.25, score.autonomous_flight.score_ratio)

        self.assertAlmostEqual(0, score.object.characteristics)
        self.assertAlmostEqual(0, score.object.geolocation)
        self.assertAlmostEqual(0, score.object.actionable)
        self.assertAlmostEqual(0, score.object.autonomy)
        self.assertAlmostEqual(0, score.object.extra_object_penalty)
        self.assertAlmostEqual(0, score.object.score_ratio)

        self.assertAlmostEqual(1, score.air_drop.drop_accuracy)
        self.assertAlmostEqual(0, score.air_drop.drive_to_location)
        self.assertAlmostEqual(0.5, score.air_drop.score_ratio)

        self.assertAlmostEqual(0.8, score.operational_excellence.score_ratio)

        self.assertAlmostEqual(0.5099777777777779, score.score_ratio)

    def test_evaluate_teams_specific_users(self):
        """Tests the evaluation of teams method with specific users."""
        user0 = User.objects.get(username='user0')
        user1 = User.objects.get(username='user1')
        config = mission_config.MissionConfig.objects.get(pk=3)

        mission_eval = mission_evaluation.evaluate_teams(config, [user0])

        self.assertEqual(1, len(mission_eval.teams))
        self.assertEqual(user0.username, mission_eval.teams[0].team.username)
