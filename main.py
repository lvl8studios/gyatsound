import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import os
import uvicorn
from telebot import telebot, types
from dotenv import load_dotenv
from handlers import register_handlers

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/{API_TOKEN}/"

WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)
app = FastAPI()

commands = [
    types.BotCommand("start", "Start the bot"),
    types.BotCommand("running_off", "Send a funny sound"),
    types.BotCommand("let_me_know", "Send a funny sound"),
    types.BotCommand("oh_my_god_bruh", "Send a funny sound"),
    types.BotCommand("wait_wait_wait", "Send a funny sound"),
    types.BotCommand("this_was_the_banker", "Send a funny sound"),
    types.BotCommand("hes_cooking", "Send a funny sound"),
]

register_handlers(bot)
bot.set_my_commands(commands)


# --- FastAPI route to receive webhook updates --- #

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    json_data = await req.json()
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return {"status": "ok"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    bot.set_my_commands(commands)
    yield
    # Shutdown
    bot.remove_webhook()

if __name__ == '__main__':
    if os.getenv('ENVIRONMENT') == 'development':
        print("Starting bot in polling mode...")
        bot.remove_webhook()
        bot.infinity_polling()
    else:
        # Production mode with webhooks
        uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8443)))