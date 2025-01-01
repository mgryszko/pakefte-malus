from unittest.mock import Mock, call

import pytest

from malus.score import *


@pytest.fixture
def athlete_a():
    return Athlete(first_name="A", last_name="AAA")

@pytest.fixture
def athlete_b():
    return Athlete(first_name="B", last_name="BBB")

@pytest.fixture
def athlete_c():
    return Athlete(first_name="C", last_name="CCC")


def test_malus():
    assert pakefte_malus(22.5, timedelta(hours=1)) == 0.0
    assert pakefte_malus(112.5, timedelta(hours=5)) == 0.0
    assert pakefte_malus(0, timedelta(hours=1)) == 22.5
    assert pakefte_malus(25, timedelta(hours=1)) == 2.5

    assert pakefte_malus(20, timedelta(hours=1)) == pytest.approx(2.5, abs=0.001)
    assert pakefte_malus(118.09, timedelta(hours=5, minutes=16, seconds=41)) == pytest.approx(0.666, abs=0.001)
    assert pakefte_malus(55.03, timedelta(hours=1, minutes=59)) == pytest.approx(10.405, abs=0.001)
    assert pakefte_malus(87.514, timedelta(hours=3, minutes=18, seconds=35)) == pytest.approx(13.045, abs=0.001)

class TestMalusByAthlete:
    @pytest.fixture
    def mocked_malus(self):
        return Mock()

    @pytest.fixture
    def noop_malus(self) -> Callable[[float, timedelta], float]:
        return lambda _distance, _time: 0.0

    def test_empty_activities(self, noop_malus, athlete_a):
        activities = []
        assert MalusByAthlete(malus=noop_malus)(activities=activities, athletes=[athlete_a]) == {}

    def test_empty_athletes(self, noop_malus, athlete_a):
        activities = [ride(athlete=athlete_a, distance_km=10.0, time=timedelta(hours=1))]
        assert MalusByAthlete(malus=noop_malus)(activities=activities, athletes=[]) == {}

    def test_not_a_ride(self, noop_malus, athlete_a):
        activities = [activity(type="Not a ride")]
        assert MalusByAthlete(malus=noop_malus)(activities=activities, athletes=[athlete_a]) == {}

    def test_below_cutoff_distance(self, noop_malus, athlete_a):
        activities = [ride(distance_km=0.999)]
        assert MalusByAthlete(malus=noop_malus)(activities=activities, athletes=[athlete_a]) == {}

    def test_more_activities_than_limits(self, athlete_a, athlete_b, athlete_c, mocked_malus):
        mocked_malus.side_effect = [1.0, 2.0]
        activities = [
            ride(athlete=athlete_a, distance_km=10.0, time=timedelta(hours=1)),
            ride(athlete=athlete_a, distance_km=20.0, time=timedelta(minutes=30)),
            ride(athlete=athlete_b, distance_km=11.0, time=timedelta(minutes=45)),
            ride(athlete=athlete_a, distance_km=30.0, time=timedelta(minutes=15)),
            ride(athlete=athlete_b, distance_km=12.0, time=timedelta(minutes=14)),
        ]
        expected = {
            athlete_a: Malus(rides=CumulativeRides(count=2, distance_km=30.0, time=timedelta(hours=1, minutes=30)), malus=1.0),
            athlete_b: Malus(rides=CumulativeRides(count=2, distance_km=23.0, time=timedelta(minutes=59)), malus=2.0),
        }

        result = MalusByAthlete(
            max_rides_per_athlete=2,
            activity_cutoff_distance_km=10.0,
            malus=mocked_malus
        )(activities=activities, athletes=[athlete_a, athlete_b, athlete_c])

        assert result == expected
        mocked_malus.assert_has_calls([
            call(30.0, timedelta(hours=1, minutes=30)),
            call(23.0, timedelta(minutes=59)),
        ])


def test_filter(athlete_a, athlete_b, athlete_c):
    rides = {
        athlete_a: malus(rides=cumulative_rides(distance_km=100.0)),
        athlete_b: malus(rides=cumulative_rides(distance_km=99.999)),
        athlete_c: malus(rides=cumulative_rides(distance_km=100.001)),
    }

    filtered_rides, excluded_athletes = filter_rides_above_cutoff_distance(
        malus_by_athlete=rides,
        rides_cutoff_distance_km=100.0
    )

    expected_rides = {
        athlete_a: malus(rides=cumulative_rides(distance_km=100.0)),
        athlete_c: malus(rides=cumulative_rides(distance_km=100.001)),
    }
    expected_excluded = [athlete_b]

    assert filtered_rides == expected_rides
    assert excluded_athletes == expected_excluded


def ride(**kwargs) -> Activity:
    return activity(**({"type": "Ride"} | kwargs))


def activity(**kwargs) -> Activity:
    empty_activity = {
        "type": None,
        "distance_km": None,
        "time": None,
        "athlete": None,
    }
    return Activity(**(empty_activity | kwargs))


def malus(**kwargs) -> Malus:
    return Malus(**({"rides": None, "malus": None} | kwargs))


def cumulative_rides(**kwargs) -> CumulativeRides:
    empty_rides = {
        "count": None,
        "distance_km": None,
        "time": None,
    }
    return CumulativeRides(**(empty_rides | kwargs))
