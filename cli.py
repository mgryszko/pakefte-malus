##!/usr/bin/env python3

import argparse
from pprint import PrettyPrinter

from stravalib.client import Client

from score import malus_by_athlete
from strava_client import get_club_activities

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--access-token", type=str, required=True)
args = parser.parse_args()

client = Client()
client.access_token = args.access_token

CLUB_ID = 1212
LIMIT = 100
CUTOFF_DISTANCE_KM = 10_000

activities = get_club_activities(client, CLUB_ID, LIMIT)
malus_by_athlete = malus_by_athlete(activities, CUTOFF_DISTANCE_KM)

pp = PrettyPrinter()
pp.pprint(malus_by_athlete)
