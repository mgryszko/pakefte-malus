from typing import Iterable

import stravalib.model

from malus.score import Activity, Athlete


def get_club_activities(client: stravalib.client.Client, club_id: int) -> Iterable[Activity]:
    activities = client.get_club_activities(club_id)
    return map(_to_activity, activities)


def get_club_athletes(client: stravalib.client.Client, club_id: int) -> Iterable[Athlete]:
    members = client.get_club_members(club_id)
    return map(_to_athlete, members)


def _to_activity(strava_activity: stravalib.model.Activity) -> Activity:
    return Activity(
        type=strava_activity.type,
        distance_km=strava_activity.distance.get_num() / 1000,
        time=strava_activity.moving_time,
        athlete=Athlete(first_name=strava_activity.athlete.firstname, last_name=strava_activity.athlete.lastname),
    )


def _to_athlete(strava_athlete: stravalib.model.Athlete) -> Athlete:
    return Athlete(
        first_name=strava_athlete.firstname,
        last_name=strava_athlete.lastname,
    )
