from datetime import timedelta
from typing import Iterable

import stravalib
from stravalib.strava_model import ClubActivity

from malus.score import Activity, Athlete


def get_club_activities(client: stravalib.client.Client, club_id: int) -> Iterable[Activity]:
    activities = client.get_club_activities(club_id)
    return map(_to_activity, activities)


def _to_activity(strava_activity: ClubActivity) -> Activity:
    return Activity(
        type=strava_activity.sport_type.root,
        distance_km=strava_activity.distance / 1000,
        time=timedelta(seconds=strava_activity.moving_time),
        athlete=Athlete(first_name=strava_activity.athlete.firstname, last_name=strava_activity.athlete.lastname),
    )
