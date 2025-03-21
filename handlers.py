import os


def register_handlers(bot):
    """Register all handlers here"""

    def create_voice_sender(filename):
        """Helper function to create voice sending handlers"""
        def send_voice(message):
            try:
                # Send voice file
                with open(f'sounds/{filename}', 'rb') as voice:
                    # Check if message is a reply
                    reply_params = None
                    if message.reply_to_message:
                        reply_params = {"message_id": message.reply_to_message.message_id}
                    bot.send_voice(message.chat.id, voice, reply_parameters=reply_params)
                # Delete the command message
                bot.delete_message(message.chat.id, message.message_id)
            except FileNotFoundError:
                bot.reply_to(message, "Sorry, this sound file is missing 😢")
            except IOError:
                bot.reply_to(message, "Sorry, there was an error playing this sound 😕")
        return send_voice

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        welcome_message = (
        "Welcome to GyatSound Bot!\n"
        "Troll your friends with funny sounds!\n\n"
        "Use /help to see all available commands."
        )
        bot.reply_to(message, welcome_message)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        # Get all available sound commands and format them nicely
        sound_commands = [f"/{os.path.splitext(f)[0]} - {os.path.splitext(f)[0].replace('_', ' ').title()}" 
                         for f in os.listdir('sounds') 
                         if f.endswith('.mp3')]
        
        help_message = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "\nSound commands:\n" +
            "\n".join(sound_commands)
        )
        bot.reply_to(message, help_message)

    # Dynamically register voice commands for all MP3 files
    for sound_file in os.listdir('sounds'):
        if sound_file.endswith('.mp3'):
            command = os.path.splitext(sound_file)[0]  # Remove .mp3 extension
            bot.message_handler(commands=[command])(create_voice_sender(sound_file))