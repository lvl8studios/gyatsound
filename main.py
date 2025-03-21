import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import os
import uvicorn
from telebot import telebot, types
from dotenv import load_dotenv
from handlers import register_handlers, get_commands
from datetime import datetime
from collections import Counter
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json

def save_metrics():
    """Save metrics to a JSON file"""
    metrics = {
        "startup_count": startup_count,
        "command_metrics": dict(command_metrics)
    }
    try:
        with open('metrics.json', 'w') as f:
            json.dump(metrics, f)
        logger.info("Metrics saved successfully")
    except Exception as e:
        logger.error(f"Failed to save metrics: {str(e)}")

def load_metrics():
    """Load metrics from JSON file"""
    global startup_count, command_metrics
    try:
        with open('metrics.json', 'r') as f:
            metrics = json.load(f)
            startup_count = metrics.get('startup_count', 0)
            command_metrics.update(metrics.get('command_metrics', {}))
        logger.info(f"Loaded metrics: startups={startup_count}, commands={dict(command_metrics)}")
    except FileNotFoundError:
        logger.info("No existing metrics file found")
    except Exception as e:
        logger.error(f"Failed to load metrics: {str(e)}")

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
_, commands = get_commands()  # Get sorted bot commands
startup_count = 0
command_metrics = Counter()
start_time = datetime.now()

register_handlers(bot)
bot.set_my_commands(commands)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # For POST requests, we need to store the body for later use
        body = None
        if request.method == "POST":
            body = await request.body()
            # Create a new request with the same body
            request = Request(request.scope, request.receive)
        
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Track webhook updates
        if request.url.path == WEBHOOK_PATH and body:
            try:
                json_data = json.loads(body)
                if 'message' in json_data and 'text' in json_data['message']:
                    command = json_data['message']['text'].split()[0]
                    global command_metrics
                    command_metrics[command] += 1
                    logger.info(f"Command tracked: {command}, Count: {command_metrics[command]}")
            except Exception as e:
                logger.error(f"Error tracking metrics: {str(e)}")
        
        logger.info(f"Request processed | Path: {request.url.path} | Time: {process_time:.2f}s")
        return response


# --- FastAPI route to receive webhook updates --- #

@app.get("/")
async def root():
    return {"status": "running", "webhook_url": WEBHOOK_URL}

@app.get("/metrics")
async def get_metrics():
    uptime = datetime.now() - start_time
    return {
        "api_startups": startup_count,
        "command_usage": dict(command_metrics),
        "uptime_seconds": uptime.total_seconds(),
        "uptime_friendly": str(uptime).split('.')[0],
        "most_used_command": command_metrics.most_common(1)[0] if command_metrics else None
    }

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    try:
        json_data = await req.json()
        logger.info(f"Received update: {json_data}")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {"status": "ok"}
    except ValueError as e:
        logger.error(f"Invalid JSON data: {str(e)}")
        return {"status": "error", "message": "Invalid JSON"}
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        load_metrics()  # Load existing metrics
        global startup_count
        startup_count += 1
        logger.info(f"API startup count: {startup_count}")
        logger.info(f"Setting webhook URL to: {WEBHOOK_URL}")
        bot.remove_webhook()
        webhook_info = bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set result: {webhook_info}")
        logger.info(f"Current metrics - Startups: {startup_count}, Commands: {dict(command_metrics)}")
        bot.set_my_commands(commands)
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")
    yield
    # Shutdown
    save_metrics()  # Save metrics before shutdown
    bot.remove_webhook()

app.add_middleware(MetricsMiddleware)

if __name__ == '__main__':
    if os.getenv('ENVIRONMENT') == 'development':
        print("Starting bot in polling mode...")
        bot.remove_webhook()
        bot.infinity_polling()
    else:
        # Production mode with webhooks
        uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8443)))