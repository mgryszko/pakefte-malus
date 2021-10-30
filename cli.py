##!/usr/bin/env python3

import argparse
from pprint import PrettyPrinter

from stravalib.client import Client

from score import rides_with_malus
from strava_client import get_club_activities

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--access-token", type=str, required=True)
args = parser.parse_args()

client = Client()
client.access_token = args.access_token

CLUB_ID = 1212
LIMIT = 100
CUTOFF_DISTANCE = 10_000

activities = get_club_activities(client, CLUB_ID, LIMIT)
rides_by_athlete = rides_with_malus(activities, CUTOFF_DISTANCE)

pp = PrettyPrinter()
pp.pprint(dict(rides_by_athlete))
