import os


def register_handlers(bot):
    """Register all handlers here"""

    def create_voice_sender(filename):
        """Helper function to create voice sending handlers"""
        def send_voice(message):
            try:
                print(f"Processing command for file: {filename}")
                print(f"Message info: chat_id={message.chat.id}, message_id={message.message_id}")
                
                # Send voice file
                with open(f'sounds/{filename}', 'rb') as voice:
                    reply_params = None
                    print("Message reply print: " + message.reply_to_message)
                    if message.reply_to_message:
                        print(f"Replying to message_id: {message.reply_to_message.message_id}")
                        reply_params = {
                            'reply_to_message_id': message.reply_to_message.message_id,
                            'allow_sending_without_reply': True
                        }
                    print(f"Reply params: {reply_params}")
                    
                    try:
                        result = bot.send_voice(message.chat.id, voice, reply_parameters=reply_params)
                        print(f"Voice message sent successfully: {result}")
                    except Exception as e:
                        print(f"Error sending voice: {str(e)}")
                        raise
                        
                print("Deleting command message...")
                bot.delete_message(message.chat.id, message.message_id)
            except FileNotFoundError:
                print(f"File not found: sounds/{filename}")
                bot.reply_to(message, "Sorry, this sound file is missing 😢")
            except IOError as e:
                print(f"IO Error: {str(e)}")
                bot.reply_to(message, "Sorry, there was an error playing this sound 😕")
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                bot.reply_to(message, "An unexpected error occurred 😕")
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