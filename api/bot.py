import telebot
from telebot import types
import os
import logging
from fastapi import FastAPI, Request

API_TOKEN = os.environ.get("BOT_TOKEN")  # Replace with your bot's API token
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT")  # Replace with your group chat ID
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # e.g., https://your-vercel-url.vercel.app

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log when the bot starts
logger.info("Bot has started working")

# Temoporary Storage
user_data = {}

# Set the webhook on startup
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")


@app.get("/")
async def read_root():
    return {
        "status": "bot is running"
    }

@app.post("/webhook")
async def telegram_webhook(req: Request):
    try:
        # Attempt to get the incoming data as JSON
        data = await req.json()

        # Parse the update using the telebot package
        update = telebot.types.Update.de_json(data)
        bot.process_new_updates([update])

        return {"status": "ok"}
    
    except Exception as e:
        # Log the error and return the status with the error message
        logger.error(f"Webhook processing failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.log(f"Webhook processing started: {e}", str(message))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Send Anonymously / በማይታወቅ", callback_data="anonymous"))
    markup.add(types.InlineKeyboardButton("Reveal Username/name / በስም", callback_data="identified"))
    
    welcome_text = (
        "Welcome to the Wku Counseling Team online mentorship.\n\n"
        "This is a safe space to share your thoughts and experiences anonymously or with your identity.\n\n"
        "WKU Evasu Fellowship የምክር ቡድን እንኳን በደህና መጡ። ይህ በማይታወቅ ወይም በስም ወደ ማኅበሩ መልእክት ለመላክ የተዘጋጀ ደህንነቱ የተጠበቀ ቦታ ነው።\n\n"
        "Choose how you want to send your message: / መልዕክትዎን ለማቅረብ ዘዴዎን ይምረጡ:"  
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["anonymous", "identified"])
def ask_for_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_data[call.message.chat.id] = {'mode': call.data}
    msg = bot.send_message(call.message.chat.id, "Please send your message (text, photo, video, or voice). / መልዕክትዎን ይላኩ (ጽሑፍ፣ ፎቶ፣ ቪዲዮ ወይም ድምፅ)")
    bot.register_next_step_handler(msg, send_message)

def send_message(message):
    mode = user_data.get(message.chat.id, {}).get('mode', 'anonymous')
    sender_info = "Anonymous / የማይታወቅ" if mode == "anonymous" else f"From: @{message.from_user.username} / ከ: @{message.from_user.username}" if message.from_user.username else f"From: {message.from_user.first_name} / ከ: {message.from_user.first_name}"
    
    if message.content_type == "text":
        bot.send_message(GROUP_CHAT_ID, f"{sender_info}\n\n{message.text}")
    elif message.content_type == "photo":
        bot.send_photo(GROUP_CHAT_ID, message.photo[-1].file_id, caption=sender_info)
    elif message.content_type == "video":
        bot.send_video(GROUP_CHAT_ID, message.video.file_id, caption=sender_info)
    elif message.content_type == "voice":
        bot.send_voice(GROUP_CHAT_ID, message.voice.file_id, caption=sender_info)
    elif message.content_type == "audio":
        bot.send_audio(GROUP_CHAT_ID, message.audio.file_id, caption=sender_info)
    else:
        bot.send_message(message.chat.id, "Unsupported message type. Please try again. / ይህ የማይደገፍ የመልዕክት አይነት ነው። እባኮትን ዳግመኛ ይሞክሩ።")
        return
    
    bot.send_message(message.chat.id, "Your message has been sent successfully! / መልዕክትዎ በተሳካ ሁኔታ ተልኳል!")

@bot.message_handler(func=lambda message: True)
def get_chat_id(message):
    print(f"Chat ID: {message.chat.id}")  # This prints the correct ID in the console
    bot.send_message(message.chat.id, f"Chat ID: {message.chat.id}")  # Sends it in the chat
