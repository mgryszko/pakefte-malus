import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from stravalib.client import Client

app = FastAPI()
client = Client()

CLIENT_ID = int(os.getenv("STRAVA_CLIENT_ID"))
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URL = f"http://localhost:8000/authorized"


@app.get("/")
def read_root():
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return RedirectResponse(authorize_url)


@app.get("/authorized")
def get_code(state=None, code=None, scope=None):
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    return token_response
