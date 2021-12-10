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
from malus.strava_client import get_club_athletes, get_club_activities

CLIENT_ID = int(os.getenv("STRAVA_CLIENT_ID"))
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STATE_ENCRYPTION_KEY = os.getenv("STRAVA_OAUTH_STATE_ENCRYPTION_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
REDIRECT_URL = f"{os.getenv('STRAVA_OAUTH_REDIRECT_URL', 'http://localhost:' + str(PORT))}/malus"

CLUB_ID = int(os.getenv("CLUB_ID"))
MAX_RIDES_PER_ATHLETE = int(os.getenv("MAX_RIDES_PER_ATHLETE"))
ACTIVITY_CUTOFF_DISTANCE_KM = int(os.getenv("ACTIVITY_CUTOFF_DISTANCE_KM"))
RIDES_CUTOFF_DISTANCE_KM = int(os.getenv("RIDES_CUTOFF_DISTANCE_KM"))

app = FastAPI()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
crypto = Crypto(STATE_ENCRYPTION_KEY)

HELP_MESSAGE = f"""Calculo el <i>malus</i> de Pakefte: 1 punto negativo por cada 1 km/h de desviación de la media de 22,5 km/h por cada hora de actividad. 
Ejemplo: una ruta de 50 km hecha en 2 horas (25 km/h de media) da el malus de 5.

Tengo en cuenta:
- únicamente las actividades de bicicleta
- las últimas {MAX_RIDES_PER_ATHLETE} actividades de cada Pakeftero con la distancia individual >= {ACTIVITY_CUTOFF_DISTANCE_KM} km y que sumen más de {RIDES_CUTOFF_DISTANCE_KM} km
- todas las actividades del club de Pakefte devueltas por la API de Strava"""

REDIRECT_TO_TELEGRAM_HTML = """<html>
    <head><script>window.location.href = "https://t.me/pakeftemalusbot"</script></head>
    <body>Redirecting to Telegram...</body>
</html>"""


@app.post("/")
async def handle_bot_message(request: Request):
    update = Update.de_json(await request.json(), bot)

    if update.message:
        command, message = update.message.text, update.message
    elif update.callback_query:
        command, message = update.callback_query.data, update.callback_query.message
    else:
        raise ValueError("Neither message nor callback_query received in the request")

    if command == "malus":
        client = Client()
        authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL,
                                                 state=crypto.encrypt(message.chat.id))
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("¡Vamos!", url=authorize_url)]])
        message.reply_text("Autoriza el acceso a Strava", reply_markup=reply_markup)
    elif command == "/start" or command == "ayuda":
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Malus", callback_data="malus")]])
        message.reply_html(HELP_MESSAGE, reply_markup=reply_markup)
    else:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Ayuda", callback_data="ayuda")]])
        message.reply_html(f"No te he entendido", reply_markup=reply_markup)

    return Response(status_code=200)


@app.get("/")
def authorize():
    client = Client()
    authorize_url = client.authorization_url(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    return RedirectResponse(authorize_url)


@app.get("/malus")
def get_pakefte_malus(code=None, state=None):
    client = Client()
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    client.access_token = token_response["access_token"]

    activities = get_club_activities(client, CLUB_ID)
    athletes = get_club_athletes(client, CLUB_ID)
    malus = malus_by_athlete(max_rides_per_athlete=MAX_RIDES_PER_ATHLETE,
                             activity_cutoff_distance_km=ACTIVITY_CUTOFF_DISTANCE_KM)(activities, athletes)
    malus, excluded_athletes = filter_rides_above_cutoff_distance(malus, RIDES_CUTOFF_DISTANCE_KM)
    sorted_malus = _sorted_by_malus_desc(malus)
    if state:
        bot.send_message(chat_id=crypto.decrypt(state),
                         text=_athlete_malus_to_telegram_msg(sorted_malus, excluded_athletes),
                         parse_mode=PARSEMODE_HTML)
        return HTMLResponse(content=REDIRECT_TO_TELEGRAM_HTML, status_code=200)
    else:
        return Response(content=_athlete_malus_to_json(sorted_malus, excluded_athletes), status_code=200, media_type="application/json")


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
