import os
from telebot.types import ReplyParameters, Message, BotCommand
from telebot.apihelper import ApiTelegramException
from db import increment_command, get_stats, init_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get authorized users from environment variable
AUTHORIZED_USERS = [
    int(user_id.strip()) 
    for user_id in os.getenv('AUTHORIZED_USER_IDS', '').split(',') 
    if user_id.strip()
]

def is_authorized(user_id: int) -> bool:
    """Check if a user is authorized to use restricted commands"""
    return user_id in AUTHORIZED_USERS

def get_commands():
    """Get sorted commands for both help display and bot registration"""
    # Get all sound files
    sound_files = sorted([f for f in os.listdir('sounds') if f.endswith('.mp3')])
    
    # Create formatted commands for help display
    help_commands = [
        f"/{os.path.splitext(f)[0]} - {os.path.splitext(f)[0].replace('_', ' ').title()}" 
        for f in sound_files
    ]
    
    # Create bot commands list
    bot_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show available commands"),
        BotCommand("stats", "Show command usage statistics"),
    ]
    bot_commands.extend(
        BotCommand(os.path.splitext(f)[0], "Send a funny sound")
        for f in sound_files
    )
    
    return help_commands, bot_commands

def register_handlers(bot):
    """Register all handlers here"""
    init_db()  # Initialize the database
    # Get sorted command lists
    help_commands, _ = get_commands()

    def is_command_for_me(message: Message, bot_username: str) -> bool:
        """Check if the command was meant for this bot"""
        if not message.text:
            return False
        command_parts = message.text.split('@')
        if len(command_parts) == 1:  # No @ in command
            return True
        return command_parts[1].lower() == bot_username.lower()

    def create_voice_sender(filename):
        """Helper function to create voice sending handlers"""
        def send_voice(message):
            try:
                command = message.text.split('@')[0][1:]  # Extract command without / and @bot
                increment_command(command)  # Track command usage
                print(f"Processing command for file: {filename}")
                print(f"Message info: chat_id={message.chat.id}, message_id={message.message_id}")
                
                # Send voice file
                with open(f'sounds/{filename}', 'rb') as voice:
                    reply_parameters = None
                    try:
                        # Try to get message_id directly
                        reply_msg_id = message.reply_to_message.message_id
                        if reply_msg_id:
                            reply_parameters = ReplyParameters(
                                message_id=reply_msg_id,
                                chat_id=message.chat.id,
                                allow_sending_without_reply=True
                            )
                    except (AttributeError, TypeError):
                        # Not a reply message or couldn't get message_id
                        pass
                    print(f"Reply parameters: {reply_parameters}")
                    
                    try:
                        result = bot.send_voice(
                            chat_id=message.chat.id,
                            voice=voice,
                            reply_parameters=reply_parameters
                        )
                        print(f"Voice message sent successfully: {result}")
                    except Exception as e:
                        print(f"Error sending voice: {str(e)}")
                        raise
                        
                print("Deleting command message...")
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except ApiTelegramException as e:
                    if "message can't be deleted" in str(e).lower():
                        bot.reply_to(message, "⚠️ I need admin rights to delete messages!")
                    else:
                        raise
            except FileNotFoundError:
                print(f"File not found: sounds/{filename}")
                bot.reply_to(message, "⚠️ Sorry, this sound file is missing")
            except IOError as e:
                print(f"IO Error: {str(e)}")
                bot.reply_to(message, "⚠️ Sorry, there was an error playing this sound")
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                bot.reply_to(message, "⚠️ An unexpected error occurred")
        return send_voice

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        if not is_command_for_me(message, bot.get_me().username):
            return
        increment_command('start')
        welcome_message = (
        "Welcome to GyatSound Bot!\n"
        "Troll your friends with funny sounds!\n\n"
        "Use /help to see all available commands. \n\n"

        "To enjoy the full functionality of GyatSound Bot, please give it admin rights in your group to delete messages."
        )
        bot.reply_to(message, welcome_message)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        if not is_command_for_me(message, bot.get_me().username):
            return
        increment_command('help')
        help_message = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "\nSound commands:\n" +
            "\n".join(help_commands)
        )
        bot.reply_to(message, help_message)

    @bot.message_handler(commands=['stats'])
    def send_stats(message):
        if not is_command_for_me(message, bot.get_me().username):
            return
        
        # Check if user is authorized
        if not is_authorized(message.from_user.id):
            bot.reply_to(message, "⚠️ You are not authorized to use this command.")
            return
            
        increment_command('stats')
        stats = get_stats()
        if not stats:
            bot.reply_to(message, "No commands have been used yet!")
            return
        
        total_uses = sum(count for _, count in stats)
        most_used = stats[0]  # First item since results are ordered by usage_count DESC
        
        stats_message = (
            "📊 Command Statistics:\n\n"
            f"Total commands used: {total_uses}\n"
            f"Most used command: /{most_used[0]} ({most_used[1]} times)\n\n"
            "Top 5 commands:\n" +
            "\n".join(f"/{cmd} - {count} times" for cmd, count in stats[:5])
        )
        bot.reply_to(message, stats_message)

    # Dynamically register voice commands for all MP3 files
    for sound_file in os.listdir('sounds'):
        if sound_file.endswith('.mp3'):
            command = os.path.splitext(sound_file)[0]  # Remove .mp3 extension
            bot.message_handler(commands=[command])(create_voice_sender(sound_file))