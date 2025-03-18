import os


def register_handlers(bot):
    """Register all handlers here"""

    def create_audio_sender(filename):
        """Helper function to create audio sending handlers"""
        def send_audio(message):
            try:
                with open(f'sounds/{filename}', 'rb') as audio:
                    bot.send_audio(message.chat.id, audio)
            except FileNotFoundError:
                bot.reply_to(message, "Sorry, this sound file is missing 😢")
            except IOError:
                bot.reply_to(message, "Sorry, there was an error playing this sound 😕")
        return send_audio

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

    # Dynamically register audio commands for all MP3 files
    for sound_file in os.listdir('sounds'):
        if sound_file.endswith('.mp3'):
            command = os.path.splitext(sound_file)[0]  # Remove .mp3 extension
            bot.message_handler(commands=[command])(create_audio_sender(sound_file))