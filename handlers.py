def register_handlers(bot):
    """Register all handlers here"""

    def create_audio_sender(filename):
        """Helper function to create audio sending handlers"""
        def send_audio(message):
            try:
                with open(f'sounds/{filename}.mp3', 'rb') as audio:
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
        "Troll your friends with funny sounds!\n"
        )
        bot.reply_to(message, welcome_message)

    @bot.message_handler(commands=['help'])
    def send_help(message):
        help_message = (
            "Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "\nSound commands:\n"
            "/running_off - Running off sound\n"
            "/let_me_know - Let me know sound\n"
            "/oh_my_god_bruh - Oh my god sound\n"
            "/wait_wait_wait - Wait wait wait sound\n"
            "/this_was_the_banker - This was the banker sound\n"
            "/hes_cooking - He's cooking sound"
        )
        bot.reply_to(message, help_message)

    # Register all audio commands
    bot.message_handler(commands=['running_off'])(create_audio_sender('running-off'))
    bot.message_handler(commands=['let_me_know'])(create_audio_sender('let-me-know'))
    bot.message_handler(commands=['oh_my_god_bruh'])(create_audio_sender('oh-my-god-bruh'))
    bot.message_handler(commands=['wait_wait_wait'])(create_audio_sender('wait-wait-wait'))
    bot.message_handler(commands=['this_was_the_banker'])(create_audio_sender('this-was-the-banker'))
    bot.message_handler(commands=['hes_cooking'])(create_audio_sender('hes-cooking'))