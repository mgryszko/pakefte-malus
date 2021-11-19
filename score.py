from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, Callable

CANONICAL_SPEED_KMH = 22.5


@dataclass(frozen=True)
class Malus:
    distance_km: float
    avg_speed_kmh: float
    malus: float


def pakefte_malus(distance_km: float, time: timedelta) -> Malus:
    time_h = time.total_seconds() / 3600
    avg_speed_kmh = distance_km / time_h
    malus = abs(avg_speed_kmh - CANONICAL_SPEED_KMH) * time_h
    return Malus(distance_km=distance_km, avg_speed_kmh=avg_speed_kmh, malus=malus)


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


def malus_by_athlete(activities: Iterable[Activity], cutoff_distance_km: float, malus: Callable[[float, float], Malus]=pakefte_malus) -> dict:
    rides = [activity for activity in activities if activity.type == "Ride" and activity.distance_km >= cutoff_distance_km]
    rides_by_athlete = {}
    for ride in rides:
        (distance_km, time) = rides_by_athlete.get(ride.athlete, (0.0, timedelta(0)))
        rides_by_athlete[ride.athlete] = (distance_km + ride.distance_km, time + ride.time)
    return {athlete: malus(*rides) for (athlete, rides) in rides_by_athlete.items()}
