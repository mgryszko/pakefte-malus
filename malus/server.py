import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from stravalib.client import Client
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import PARSEMODE_HTML

from malus.crypto import Crypto
from malus.score import malus_by_athlete, filter_rides_above_cutoff_distance
from malus.strava_client import get_club_activities

CLIENT_ID = int(os.getenv("STRAVA_CLIENT_ID"))
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STATE_ENCRYPTION_KEY = os.getenv("STRAVA_OAUTH_STATE_ENCRYPTION_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
REDIRECT_URL = f"{os.getenv('STRAVA_OAUTH_REDIRECT_URL', 'http://localhost:' + str(PORT))}/malus"

CLUB_ID = int(os.getenv("CLUB_ID"))
ACTIVITIES_LIMIT = int(os.getenv("ACTIVITIES_LIMIT"))
ACTIVITY_CUTOFF_DISTANCE_KM = int(os.getenv("ACTIVITY_CUTOFF_DISTANCE_KM"))
RIDES_CUTOFF_DISTANCE_KM = int(os.getenv("RIDES_CUTOFF_DISTANCE_KM"))

app = FastAPI()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
crypto = Crypto(STATE_ENCRYPTION_KEY)


@app.post("/")
async def authorize_telegram(request: Request):
    update = Update.de_json(await request.json(), bot)
    client = Client()
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL, state=crypto.encrypt(update.message.chat.id))
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("Authorize", url=authorize_url),
    ]])
    update.message.reply_text("Authorize", reply_markup=reply_markup)


@app.get("/")
def authorize_browser():
    client = Client()
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return RedirectResponse(authorize_url)


def _sorted_by_malus_desc(malus):
    return sorted(malus.items(), key=lambda kv: kv[1].malus, reverse=True)


def _athlete_malus_to_telegram_msg(athlete_malus, excluded_athletes):
    def to_malus_msg(athlete, malus):
        return f"""<b>{athlete.first_name} {athlete.last_name}</b>: <u>{malus.malus:.2f}</u>
{malus.rides.count} actividades, {malus.rides.distance_km:.2f} km, {malus.rides.avg_speed_kmh:.2f} km/h\n"""
    malus_msg = "\n".join([to_malus_msg(athlete, malus) for (athlete, malus) in athlete_malus])
    excluded_athletes_msg = ", ".join([f"{athlete.first_name} {athlete.last_name}" for athlete in excluded_athletes])

    return f"{malus_msg}\nMenos de {RIDES_CUTOFF_DISTANCE_KM} km: {excluded_athletes_msg}"


def _athlete_malus_to_json(malus, excluded_athletes):
    return json.dumps({
            "malus": [{f"{athlete.first_name} {athlete.last_name}": malus} for (athlete, malus) in malus],
            "excluded": [f"{athlete.first_name} {athlete.last_name}" for athlete in excluded_athletes],
        },
        indent=4,
        default=str,
    ).encode("utf-8")


@app.get("/malus")
def get_pakefte_malus(code=None, state=None):
    client = Client()
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    client.access_token = token_response["access_token"]

    activities = get_club_activities(client, CLUB_ID, ACTIVITIES_LIMIT)
    malus = malus_by_athlete(activities, ACTIVITY_CUTOFF_DISTANCE_KM)
    malus, excluded_athletes = filter_rides_above_cutoff_distance(malus, RIDES_CUTOFF_DISTANCE_KM)
    sorted_malus = _sorted_by_malus_desc(malus)
    if state:
        bot.send_message(chat_id=crypto.decrypt(state),
                         text=_athlete_malus_to_telegram_msg(sorted_malus, excluded_athletes),
                         parse_mode=PARSEMODE_HTML)
        html_content = """
<html>
    <head><script>window.location.href = "https://telegram.me/pakeftemalusbot"</script></head>
    <body>Redirecting to Telegram...</body>
</html>
"""
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return Response(content=_athlete_malus_to_json(sorted_malus, excluded_athletes), status_code=200, media_type="application/json")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
