import unittest
from unittest.mock import Mock, call

from malus.score import *


class TestMalus(unittest.TestCase):
    def test_malus(self):
        self.assertEqual(0.0, pakefte_malus(22.5, timedelta(hours=1)))
        self.assertEqual(0.0, pakefte_malus(112.5, timedelta(hours=5)))
        self.assertEqual(22.5, pakefte_malus(0, timedelta(hours=1)))
        self.assertEqual(2.5, pakefte_malus(25, timedelta(hours=1)))
        self.assertAlmostEqual(2.5, pakefte_malus(20, timedelta(hours=1)), delta=0.001)
        self.assertAlmostEqual(0.666, pakefte_malus(118.09, timedelta(hours=5, minutes=16, seconds=41)), delta=0.001)
        self.assertAlmostEqual(10.405, pakefte_malus(55.03, timedelta(hours=1, minutes=59)), delta=0.001)
        self.assertAlmostEqual(13.045, pakefte_malus(87.514, timedelta(hours=3, minutes=18, seconds=35)), delta=0.001)


class TestMalusByAthlete(unittest.TestCase):
    athleteA = Athlete(first_name="A", last_name="AAA")
    athleteB = Athlete(first_name="B", last_name="BBB")
    athleteC = Athlete(first_name="C", last_name="CCC")

    def setUp(self):
        self.malus = Mock()

    def test_empty_activities(self):
        activities = []
        self.assertEqual(malus_by_athlete(malus=None)(activities=activities, athletes=[self.athleteA]), {})

    def test_empty_athletes(self):
        activities = [ride(athlete=self.athleteA, distance_km=10.0, time=timedelta(hours=1))]
        self.assertEqual(malus_by_athlete(malus=None)(activities=activities, athletes=[]), {})

    def test_not_a_ride(self):
        activities = [activity(type="Not a Ride")]
        self.assertEqual(malus_by_athlete(malus=None)(activities=activities, athletes=[self.athleteA]), {})

    def test_below_cutoff_distance(self):
        activities = [ride(distance_km=0.999)]
        self.assertEqual(malus_by_athlete(malus=None)(activities=activities, athletes=[self.athleteA]), {})

    def test_more_activities_than_limits(self):
        self.malus.side_effect = [1.0, 2.0]
        activities = [
            ride(athlete=self.athleteA, distance_km=10.0, time=timedelta(hours=1)),
            ride(athlete=self.athleteA, distance_km=20.0, time=timedelta(minutes=30)),
            ride(athlete=self.athleteB, distance_km=11.0, time=timedelta(minutes=45)),
            ride(athlete=self.athleteA, distance_km=30.0, time=timedelta(minutes=15)),
            ride(athlete=self.athleteB, distance_km=12.0, time=timedelta(minutes=14)),
        ]
        expected = {
            self.athleteA: Malus(rides=CumulativeRides(count=2, distance_km=30.0, time=timedelta(hours=1, minutes=30)), malus=1.0),
            self.athleteB: Malus(rides=CumulativeRides(count=2, distance_km=23.0, time=timedelta(minutes=59)), malus=2.0),
        }

        self.assertEqual(expected, malus_by_athlete(max_rides_per_athlete=2,
                                                    activity_cutoff_distance_km=10.0,
                                                    malus=self.malus)(activities=activities,
                                                                      athletes=[self.athleteA, self.athleteB, self.athleteC]))

        self.malus.assert_has_calls([
            call(30.0, timedelta(hours=1, minutes=30)),
            call(23.0, timedelta(minutes=59)),
        ])


class TestFilterRides(unittest.TestCase):
    athleteA = Athlete(first_name="A", last_name="B")
    athleteB = Athlete(first_name="C", last_name="D")
    athleteC = Athlete(first_name="D", last_name="F")

    def test_filter(self):
        rides = {
            self.athleteA: malus(rides=cumulative_rides(distance_km=100.0)),
            self.athleteB: malus(rides=cumulative_rides(distance_km=99.999)),
            self.athleteC: malus(rides=cumulative_rides(distance_km=100.001)),
        }
        self.assertEqual(filter_rides_above_cutoff_distance(malus_by_athlete=rides, rides_cutoff_distance_km=100.0), ({
            self.athleteA: malus(rides=cumulative_rides(distance_km=100.0)),
            self.athleteC: malus(rides=cumulative_rides(distance_km=100.001)),
        }, [self.athleteB]))


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


def malus(**kwargs):
    return Malus(**({"rides": None, "malus": None} | kwargs))


def cumulative_rides(**kwargs):
    empty_rides = {
        "count": None,
        "distance_km": None,
        "time": None,
    }
    return CumulativeRides(**(empty_rides | kwargs))
