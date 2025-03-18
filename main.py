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

# Initialize basic commands
commands = [
    types.BotCommand("start", "Start the bot"),
    types.BotCommand("help", "Show available commands"),
]

# Dynamically add commands for each sound file
for sound_file in os.listdir('sounds'):
    if sound_file.endswith('.mp3'):
        command_name = os.path.splitext(sound_file)[0]  # Remove .mp3 extension
        commands.append(types.BotCommand(command_name, "Send a funny sound"))


register_handlers(bot)
bot.set_my_commands(commands)


# --- FastAPI route to receive webhook updates --- #

@app.get("/")
async def root():
    return {"status": "running", "webhook_url": WEBHOOK_URL}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    try:
        json_data = await req.json()
        logger.info(f"Received update: {json_data}")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info(f"Setting webhook URL to: {WEBHOOK_URL}")
        bot.remove_webhook()
        webhook_info = bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set result: {webhook_info}")
        bot.set_my_commands(commands)
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")
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