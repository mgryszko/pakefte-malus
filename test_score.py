import unittest
from unittest.mock import Mock, call

from score import *


class TestMalus(unittest.TestCase):
    def test_malus(self):
        self.assertEqual(0.0, pakefte_malus(km(22.5), timedelta(hours=1)))
        self.assertEqual(0.0, pakefte_malus(km(112.5), timedelta(hours=5)))
        self.assertAlmostEqual(22.5, pakefte_malus(km(0), timedelta(hours=1)), delta=0.001)
        self.assertAlmostEqual(2.5, pakefte_malus(km(25), timedelta(hours=1)), delta=0.001)
        self.assertAlmostEqual(2.5, pakefte_malus(km(20), timedelta(hours=1)), delta=0.001)
        self.assertAlmostEqual(0.666, pakefte_malus(km(118.09), timedelta(hours=5, minutes=16, seconds=41)), delta=0.001)
        self.assertAlmostEqual(10.405, pakefte_malus(km(55.03), timedelta(hours=1, minutes=59)), delta=0.001)
        self.assertAlmostEqual(13.045, pakefte_malus(km(87.514), timedelta(seconds=11915)), delta=0.001)


def km(d):
    return d * 1000


class TestRidesWithMalus(unittest.TestCase):
    def setUp(self):
        self.malus = Mock()

    def test_empty_activities(self):
        activities = []
        self.assertEqual(rides_with_malus(activities=activities, cutoff_distance_m=0, malus=None), {})

    def test_not_a_ride(self):
        activities = [activity(type="Not a Ride")]
        self.assertEqual(rides_with_malus(activities=activities, cutoff_distance_m=0, malus=None), {})

    def test_below_cutoff_distance(self):
        activities = [ride(distance_m=0.999)]
        self.assertEqual(rides_with_malus(activities=activities, cutoff_distance_m=1.0, malus=None), {})

    def test_activities(self):
        self.malus.side_effect = [100.0, 200.0, 50.0, 300.0, 75.0]
        activities = [
            ride(
                name="A's activity 1",
                distance_m=1.0,
                time=timedelta(seconds=60),
                athlete=Athlete(first_name="A", last_name="B"),
            ),
            ride(
                name="A's activity 2",
                distance_m=2.0,
                time=timedelta(seconds=120),
                athlete=Athlete(first_name="A", last_name="B"),
            ),
            ride(
                name="C's activity 1",
                distance_m=11.0,
                time=timedelta(seconds=30),
                athlete=Athlete(first_name="C", last_name="D"),
            ),
            ride(
                name="A's activity 3",
                distance_m=3.0,
                time=timedelta(seconds=180),
                athlete=Athlete(first_name="A", last_name="B"),
            ),
            ride(
                name="C's activity 2",
                distance_m=12.0,
                time=timedelta(seconds=45),
                athlete=Athlete(first_name="C", last_name="D"),
            ),
        ]
        expected = {
            "A B": [
                ("A's activity 1", 1.0, timedelta(seconds=60), 100.0),
                ("A's activity 2", 2.0, timedelta(seconds=120), 200.0),
                ("A's activity 3", 3.0, timedelta(seconds=180), 300.0),
            ],
            "C D": [
                ("C's activity 1", 11.0, timedelta(seconds=30), 50.0),
                ("C's activity 2", 12.0, timedelta(seconds=45), 75.0),
            ]
        }
        self.assertEqual(expected, rides_with_malus(activities=activities, cutoff_distance_m=1.0, malus=self.malus))
        self.malus.assert_has_calls([
            call(1.0, timedelta(seconds=60)),
            call(2.0, timedelta(seconds=120)),
            call(11.0, timedelta(seconds=30)),
            call(3.0, timedelta(seconds=180)),
            call(12.0, timedelta(seconds=45)),
        ])


def ride(**kwargs):
    return activity(**({"type": "Ride"} | kwargs))


def activity(**kwargs):
    empty_activity = {
        "name": "",
        "type": None,
        "distance_m": None,
        "time": None,
        "athlete": None,
    }
    return Activity(**(empty_activity | kwargs))
