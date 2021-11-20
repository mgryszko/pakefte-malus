import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from stravalib.client import Client
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import PARSEMODE_HTML

from score import malus_by_athlete
from strava_client import get_club_activities

CLIENT_ID = int(os.getenv("STRAVA_CLIENT_ID"))
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
REDIRECT_URL = f"{os.getenv('STRAVA_OAUTH_REDIRECT_URL', 'http://localhost:' + str(PORT))}/malus"

CLUB_ID = int(os.getenv("CLUB_ID"))
ACTIVITIES_LIMIT = int(os.getenv("ACTIVITIES_LIMIT"))
CUTOFF_DISTANCE_KM = int(os.getenv("CUTOFF_DISTANCE_KM"))

app = FastAPI()
bot = Bot(token=TELEGRAM_BOT_TOKEN)


@app.post("/")
async def authorize_telegram(request: Request):
    update = Update.de_json(await request.json(), bot)
    client = Client()
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL, state=update.message.chat.id)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("Authorize", url=authorize_url),
    ]])
    update.message.reply_text("Authorize", reply_markup=reply_markup)


@app.get("/")
def authorize_browser():
    client = Client()
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return RedirectResponse(authorize_url)


def _sorted_by_malus_desc(athlete_malus):
    return sorted(athlete_malus.items(), key=lambda kv: kv[1].malus, reverse=True)


def _athlete_malus_to_json(athlete_malus):
    return json.dumps(
        [{f"{athlete.first_name} {athlete.last_name}": malus} for (athlete, malus) in athlete_malus],
        indent=4,
        default=str,
    ).encode("utf-8")


def _athlete_malus_to_telegram_msg(athlete_malus):
    def to_msg(athlete, malus):
        return f"""<b>{athlete.first_name} {athlete.last_name}</b>: <u>{malus.malus:.2f}</u>
{malus.rides.count} act., {malus.rides.distance_km:.2f} km, {malus.rides.avg_speed_kmh:.2f} km/h\n"""

    return "\n".join([to_msg(athlete, malus) for (athlete, malus) in athlete_malus])


@app.get("/malus")
def get_pakefte_malus(code=None, state=None):
    client = Client()
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    client.access_token = token_response["access_token"]

    activities = get_club_activities(client, CLUB_ID, ACTIVITIES_LIMIT)
    athlete_malus = _sorted_by_malus_desc(malus_by_athlete(activities, CUTOFF_DISTANCE_KM))
    if state:
        bot.send_message(chat_id=state, text=_athlete_malus_to_telegram_msg(athlete_malus), parse_mode=PARSEMODE_HTML)
        html_content = """
<html>
    <head><script>window.location.href = "https://telegram.me/pakeftemalusbot"</script></head>
    <body>Redirecting to Telegram...</body>
</html>
"""
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return Response(content=_athlete_malus_to_json(athlete_malus), status_code=200, media_type="application/json")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
