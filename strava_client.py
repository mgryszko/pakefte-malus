from collections.abc import Iterable

import stravalib.model

import score
from score import Activity, Athlete
from stravalib.client import Client


def _to_activity(strava_activity: stravalib.model.Activity) -> Activity:
    return Activity(
        type=strava_activity.type,
        name=strava_activity.name,
        distance_m=strava_activity.distance.get_num(),
        time=strava_activity.moving_time,
        athlete=Athlete(first_name=strava_activity.athlete.firstname, last_name=strava_activity.athlete.lastname),
    )


def get_club_activities(client: stravalib.client.Client, club_id: int, limit: int) -> Iterable[Activity]:
    activities = client.get_club_activities(club_id, limit)
    return map(_to_activity, activities)
