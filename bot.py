import os
import time
import glob  # Papkani tozalash uchun qidiruv kutubxonasi
import requests
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- BOT_TOKEN ni server sozlamalaridan qidiradi
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8934901025:AAFAv-ZCK0XSw0DdBtUuHbnEKU-Ed0Eem9I")
bot = TeleBot(BOT_TOKEN)

# Foydalanuvchilarning tanlagan tilini saqlash uchun lug'at
user_languages = {}

# 3 tilda xabarlar lug'ati
bot_strings = {
    'uz': {
        'welcome': "👋 Salom! **ViDore** botiga xush kelibsiz!\n\n📥 Menga YouTube, Instagram yoki TikTok videosining havolasini (link) yuboring, yuklab beraman!",
        'downloading': "⏳ ViDore videoni yuklab olmoqda, iltimos kuting...",
        'success': "✨ Video **ViDore** bot orqali muvaffaqiyatli yuklab olindi!",
        'error': "❌ Kechirasiz, bu linkdan videoni yuklab bo'lmadi yoki serverda cheklov bor.",
        'fallback': "⚠️ Iltimos, faqat to'g'ri video havolasini (linkini) yuboring!",
        'size_error': "⚠️ Kechirasiz, video hajmi juda katta ({size} MB).\nTelegram botlar bepul rejimda ko'pi bilan 50 MB gacha fayl yubora oladi."
    },
    'ru': {
        'welcome': "👋 Привет! Добро пожаловать в бот **ViDore**!\n\n📥 Отправьте мне ссылку на видео из YouTube, Instagram или TikTok, и я скачаю его для вас!",
        'downloading': "⏳ ViDore скачивает видео, пожалуйста, подождите...",
        'success': "✨ Видео успешно скачано через бот **ViDore**!",
        'error': "❌ Извините, не удалось скачать видео по этой ссылке или сервер заблокирован.",
        'fallback': "⚠️ Пожалуйста, отправьте корректную ссылку на видео!" ,
        'size_error': "⚠️ Извините, размер видео слишком большой ({size} МБ).\nTelegram боты в бесплатном режиме могут отправлять файлы только до 50 МБ."
    },
    'en': {
        'welcome': "👋 Hello! Welcome to **ViDore** bot!\n\n📥 Send me a YouTube, Instagram, or TikTok video link, and I will download it for you!",
        'downloading': "⏳ ViDore is downloading the video, please wait...",
        'success': "✨ Video successfully downloaded via **ViDore** bot!",
        'error': "❌ Sorry, failed to download video from this link or server restriction occurred.",
        'fallback': "⚠️ Please send a valid video link!",
        'size_error': "⚠️ Sorry, the video size is too large ({size} MB).\nTelegram bots can only send files up to 50 MB in free mode."
    }
}

# Til tugmalari
def get_lang_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    btn_uz = InlineKeyboardButton(text="🇺🇿 UZ", callback_data="lang_uz")
    btn_ru = InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang_ru")
    btn_en = InlineKeyboardButton(text="🇺🇸 EN", callback_data="lang_en")
    keyboard.add(btn_uz, btn_ru, btn_en)
    return keyboard

# /start buyrug'i
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "🌐 Bot tilini tanlang / Выберите язык бота / Choose language:", 
        reply_markup=get_lang_keyboard()
    )

# Til tanlanganda
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_lang_selection(call):
    chat_id = call.message.chat.id
    selected_lang = call.data.split('_')[1]
    
    user_languages[chat_id] = selected_lang
    welcome_text = bot_strings[selected_lang]['welcome']
    
    bot.edit_message_text(welcome_text, chat_id, call.message.message_id, parse_mode="Markdown")

# Video yuklash qismi (Tashqi API orqali Render blokirovkalarini aylanib o'tuvchi variant)
@bot.message_handler(func=lambda message: message.text.startswith(('http://', 'https://')))
def download_video_tg(message):
    chat_id = message.chat.id
    url = message.text
    
    # Majburiy til tekshiruvi
    if chat_id not in user_languages:
        bot.send_message(
            chat_id, 
            "⚠️ Botdan foydalanish uchun avval tilni tanlang!\n⚠️ Для использования бота сначала выберите язык!\n⚠️ Please choose a language first to use the bot:", 
            reply_markup=get_lang_keyboard()
        )
        return
    
    lang = user_languages[chat_id]
    status_message = bot.send_message(chat_id, bot_strings[lang]['downloading'])
    
    # Render IP-blokidan qochish uchun tekin va kuchli yuklovchi API xizmati
    api_url = f"https://api.vyt-dlp.workers.dev/download?url={url}"
    
    try:
        # API serveriga so'rov yuboramiz
        response = requests.get(api_url, timeout=30).json()
        
        if response.get("success") and response.get("download_url"):
            video_url = response["download_url"]
            
            # Videoni o'z serverimizga yuklab o'tirmasdan, Telegram'ga to'g'ridan-to'g'ri havola orqali uzatamiz.
            # Bu nafaqat tez ishlaydi, balki Render'dagi 50MB disk to'lib qolish xavfini ham yo'qotadi!
            bot.send_video(
                chat_id, 
                video_url, 
                caption=bot_strings[lang]['success'], 
                parse_mode="Markdown",
                reply_to_message_id=message.message_id
            )
            bot.delete_message(chat_id, status_message.message_id)
        else:
            bot.edit_message_text(bot_strings[lang]['error'], chat_id, status_message.message_id)
            
    except Exception as e:
        print(f"Yuklashda texnik xatolik: {e}")
        bot.edit_message_text(bot_strings[lang]['error'], chat_id, status_message.message_id)

# Boshqa matnlar kelganda
@bot.message_handler(func=lambda message: True)
def text_fallback(message):
    chat_id = message.chat.id
    
    if chat_id not in user_languages:
        bot.send_message(
            chat_id, 
            "🌐 Iltimos, avval tilni tanlang / Выберите язык / Choose language:", 
            reply_markup=get_lang_keyboard()
        )
        return

    lang = user_languages[chat_id]
    bot.reply_to(message, bot_strings[lang]['fallback'])

# Botni ishga tushirish va Render sozlamalari
if __name__ == "__main__":
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running successfully!")

    def run_dummy_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
        server.serve_forever()

    # Veb-serverni alohida oqimda yoqamiz (Render o'chib qolmasligi uchun)
    threading.Thread(target=run_dummy_server, daemon=True).start()

    print("🤖 Konfliktlar (zombi jarayonlar) tozalanmoqda...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Webhook tozalashda xato: {e}")

    print("🤖 ViDore Bot muvaffaqiyatli ishga tushdi...")
    bot.polling(none_stop=True, interval=0, timeout=20)
