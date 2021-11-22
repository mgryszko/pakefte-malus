from typing import Iterable

import stravalib.model

from malus.score import Activity, Athlete


def _to_activity(strava_activity: stravalib.model.Activity) -> Activity:
    return Activity(
        type=strava_activity.type,
        distance_km=strava_activity.distance.get_num() / 1000,
        time=strava_activity.moving_time,
        athlete=Athlete(first_name=strava_activity.athlete.firstname, last_name=strava_activity.athlete.lastname),
    )


def get_club_activities(client: stravalib.client.Client, club_id: int, limit: int) -> Iterable[Activity]:
    activities = client.get_club_activities(club_id, limit)
    return map(_to_activity, activities)
