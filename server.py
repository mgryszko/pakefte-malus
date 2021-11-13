import os
import uvicorn

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from stravalib.client import Client
from strava_client import get_club_activities
from score import rides_with_malus

app = FastAPI()

CLIENT_ID = int(os.getenv("STRAVA_CLIENT_ID"))
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
PORT = int(os.getenv("PORT", 8080))
REDIRECT_URL = f"{os.getenv('STRAVA_OAUTH_REDIRECT_PROTOCOL', 'http')}://{os.getenv('STRAVA_OAUTH_REDIRECT_HOST', 'localhost')}:{os.getenv('STRAVA_OAUTH_REDIRECT_PORT', PORT)}/malus"

CLUB_ID = int(os.getenv("CLUB_ID"))
ACTIVITIES_LIMIT = int(os.getenv("ACTIVITIES_LIMIT"))
CUTOFF_DISTANCE_M = int(os.getenv("CUTOFF_DISTANCE_M"))


@app.get("/")
def authorize():
    client = Client()
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return RedirectResponse(authorize_url)


@app.get("/malus")
def get_pakefte_malus(code=None):
    client = Client()
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    client.access_token = token_response["access_token"]

    activities = get_club_activities(client, CLUB_ID, ACTIVITIES_LIMIT)
    return rides_with_malus(activities, CUTOFF_DISTANCE_M)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)