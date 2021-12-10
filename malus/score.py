from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, Callable

CANONICAL_SPEED_KMH = 22.5


def pakefte_malus(distance_km: float, time: timedelta) -> float:
    time_h = time.total_seconds() / 3600
    avg_speed_kmh = distance_km / time_h
    return abs(avg_speed_kmh - CANONICAL_SPEED_KMH) * time_h


@dataclass(frozen=True)
class Athlete:
    first_name: str
    last_name: str

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


@dataclass(frozen=True)
class Activity:
    type: str
    distance_km: float
    time: timedelta
    athlete: Athlete


@dataclass(frozen=True)
class CumulativeRides:
    count: int
    distance_km: float
    time: timedelta

    @property
    def avg_speed_kmh(self):
        return self.distance_km / (self.time.total_seconds() / 3600)

    @classmethod
    def empty(cls):
        return CumulativeRides(0, 0.0, timedelta(0))

    def add_ride(self, distance_km, time):
        return CumulativeRides(
            count=self.count + 1,
            distance_km=self.distance_km + distance_km,
            time=self.time + time,
        )


@dataclass(frozen=True)
class Malus:
    rides: CumulativeRides
    malus: float


class malus_by_athlete:
    def __init__(self, max_rides_per_athlete: int = 10,
        activity_cutoff_distance_km: float = 10,
        malus: Callable[[float, float], Malus] = pakefte_malus):
        self.max_rides_per_athlete = max_rides_per_athlete
        self.activity_cutoff_distance_km = activity_cutoff_distance_km
        self.malus = malus

    def __call__(self, activities: Iterable[Activity], athletes: Iterable[Athlete]) -> dict[Athlete, Malus]:
        rides = filter(lambda a: a.type == "Ride" and a.distance_km >= self.activity_cutoff_distance_km, activities)

        rides_by_athlete = {}
        rem_rides_by_athlete = {athlete: self.max_rides_per_athlete for athlete in athletes}
        while len(rem_rides_by_athlete) > 0 and (ride := next(rides, None)) is not None:
            rem_athlete_rides = rem_rides_by_athlete.get(ride.athlete, 0)
            if rem_athlete_rides > 0:
                cumulative_rides = rides_by_athlete.get(ride.athlete, CumulativeRides.empty())
                rides_by_athlete[ride.athlete] = cumulative_rides.add_ride(ride.distance_km, ride.time)
            _decrease_remaining(rem_rides_by_athlete, ride.athlete)

        return {athlete: Malus(rides=rides, malus=self.malus(rides.distance_km, rides.time))
                for (athlete, rides) in rides_by_athlete.items()}


def _decrease_remaining(remaining_athletes: dict[Athlete, int], athlete: Athlete):
    remaining = remaining_athletes.get(athlete, 0) - 1
    if remaining > 0:
        remaining_athletes[athlete] = remaining
    else:
        remaining_athletes.pop(athlete, None)


def filter_rides_above_cutoff_distance(malus_by_athlete: dict[Athlete, Malus], rides_cutoff_distance_km: float) -> \
    tuple[dict[Athlete, Malus], list[Athlete]]:
    filtered_malus = {athlete: malus for (athlete, malus) in malus_by_athlete.items() if
                      malus.rides.distance_km >= rides_cutoff_distance_km}
    excluded_athletes = [athlete for (athlete, malus) in malus_by_athlete.items() if malus.rides.distance_km < rides_cutoff_distance_km]
    return filtered_malus, excluded_athletes


def _cumulative_rides_by_athlete(rides: Iterable[Activity]) -> dict[Athlete, CumulativeRides]:
    rides_by_athlete = {}
    for ride in rides:
        cumulative_rides = rides_by_athlete.get(ride.athlete, CumulativeRides.empty())
        rides_by_athlete[ride.athlete] = cumulative_rides.add_ride(ride.distance_km, ride.time)
    return rides_by_athlete
