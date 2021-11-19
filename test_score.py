import unittest
from unittest.mock import Mock, call

from score import *


class TestMalus(unittest.TestCase):
    def test_malus(self):
        self.assertEqual(Malus(distance_km=22.5, avg_speed_kmh=22.5, malus=0.0), pakefte_malus(22.5, timedelta(hours=1)))
        self.assertEqual(Malus(distance_km=112.5, avg_speed_kmh=22.5, malus=0.0), pakefte_malus(112.5, timedelta(hours=5)))
        self.assertEqual(Malus(distance_km=0, avg_speed_kmh=0.0, malus=22.5), pakefte_malus(0, timedelta(hours=1)))
        self.assertEqual(Malus(distance_km=25, avg_speed_kmh=25.0, malus=2.5), pakefte_malus(25, timedelta(hours=1)))
        self.assertAlmostEqual(Malus(distance_km=20, avg_speed_kmh=20.0, malus=2.5), pakefte_malus(20, timedelta(hours=1)))
        self.assertAlmostEqual(Malus(distance_km=118.09, avg_speed_kmh=22.374, malus=0.666),
                               pakefte_malus(118.09, timedelta(hours=5, minutes=16, seconds=41)))
        self.assertAlmostEqual(Malus(distance_km=55.03, avg_speed_kmh=27.746, malus=10.405),
                               pakefte_malus(55.03, timedelta(hours=1, minutes=59)))
        self.assertAlmostEqual(Malus(distance_km=87.514, avg_speed_kmh=26.441, malus=13.045),
                               pakefte_malus(87.514, timedelta(hours=3, minutes=18, seconds=35)))

    def assertAlmostEqual(self, first: Malus, second: Malus):
        if first == second:
            return

        self._assertAlmostEquals(first, second, "distance_km")
        self._assertAlmostEquals(first, second, "avg_speed_kmh")
        self._assertAlmostEquals(first, second, "malus")

    def _assertAlmostEquals(self, first, second, property):
        delta = 0.001
        diff = abs(first.__dict__[property] - second.__dict__[property])
        if diff > delta:
            msg = f"{repr(first)} != {repr(second)} within {repr(delta)} delta ({repr(diff)} difference)"
            raise self.failureException(msg)


class TestRidesWithMalus(unittest.TestCase):
    athleteA = Athlete(first_name="A", last_name="B")
    athleteB = Athlete(first_name="C", last_name="D")

    def setUp(self):
        self.malus = Mock()

    def test_empty_activities(self):
        activities = []
        self.assertEqual(malus_by_athlete(activities=activities, cutoff_distance_km=0, malus=None), {})

    def test_not_a_ride(self):
        activities = [activity(type="Not a Ride")]
        self.assertEqual(malus_by_athlete(activities=activities, cutoff_distance_km=0, malus=None), {})

    def test_below_cutoff_distance(self):
        activities = [ride(distance_km=0.999)]
        self.assertEqual(malus_by_athlete(activities=activities, cutoff_distance_km=1.0, malus=None), {})

    def test_activities(self):
        self.malus.side_effect = [
            Malus(distance_km=60.0, avg_speed_kmh=25.0, malus=1.0),
            Malus(distance_km=23.0, avg_speed_kmh=15.0, malus=2.0)
        ]
        activities = [
            ride(distance_km=10.0, time=timedelta(hours=1), athlete=self.athleteA),
            ride(distance_km=20.0, time=timedelta(minutes=30), athlete=self.athleteA),
            ride(distance_km=11.0, time=timedelta(minutes=45), athlete=self.athleteB),
            ride(distance_km=30.0, time=timedelta(minutes=15), athlete=self.athleteA),
            ride(distance_km=12.0, time=timedelta(minutes=14), athlete=self.athleteB),
        ]
        expected = {
            self.athleteA: Malus(distance_km=60.0, avg_speed_kmh=25.0, malus=1.0),
            self.athleteB: Malus(distance_km=23.0, avg_speed_kmh=15.0, malus=2.0),
        }
        self.assertEqual(expected, malus_by_athlete(activities=activities, cutoff_distance_km=10.0, malus=self.malus))
        self.malus.assert_has_calls([
            call(60.0, timedelta(hours=1, minutes=45)),
            call(23.0, timedelta(minutes=59)),
        ])


def ride(**kwargs):
    return activity(**({"type": "Ride"} | kwargs))


def activity(**kwargs):
    empty_activity = {
        "type": None,
        "distance_km": None,
        "time": None,
        "athlete": None,
    }
    return Activity(**(empty_activity | kwargs))
