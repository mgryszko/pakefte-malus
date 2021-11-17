import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from stravalib.client import Client

from score import rides_with_malus
from strava_client import get_club_activities
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton

CLIENT_ID = int(os.getenv("STRAVA_CLIENT_ID"))
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
REDIRECT_URL = f"{os.getenv('STRAVA_OAUTH_REDIRECT_URL', 'http://localhost:' + str(PORT))}/malus"

CLUB_ID = int(os.getenv("CLUB_ID"))
ACTIVITIES_LIMIT = int(os.getenv("ACTIVITIES_LIMIT"))
CUTOFF_DISTANCE_M = int(os.getenv("CUTOFF_DISTANCE_M"))

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


@app.get("/malus")
def get_pakefte_malus(code=None, state=None):
    client = Client()
    token_response = client.exchange_code_for_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=code)
    client.access_token = token_response["access_token"]

    activities = get_club_activities(client, CLUB_ID, ACTIVITIES_LIMIT)
    malus = rides_with_malus(activities, CUTOFF_DISTANCE_M)
    if state is not None:
        bot.send_message(chat_id=state, text=json.dumps(malus, default=str)[0:100])
        html_content = """
<html>
    <head><script>window.location.href = "https://telegram.me/pakeftemalusbot"</script></head>
    <body>Redirecting to Telegram...</body>
</html>
"""
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return malus


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
