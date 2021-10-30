from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta

CANONICAL_SPEED_KMH = 22.5


def pakefte_malus(distance_m: int | float, time: timedelta) -> float:
    time_h = time.total_seconds() / 3600
    avg_speed_kmh = (distance_m / 1000) / time_h
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
    name: float
    distance_m: int | float
    time: timedelta
    athlete: Athlete


def rides_with_malus(activities, cutoff_distance_m, malus=pakefte_malus):
    rides = [activity for activity in activities if activity.type == "Ride" and activity.distance_m >= cutoff_distance_m]
    rides_by_athlete = defaultdict(list)
    for ride in rides:
        rides_by_athlete[ride.athlete.full_name()].append((ride.name, ride.distance_m, ride.time, malus(ride.distance_m, ride.time)))
    return dict(rides_by_athlete)
