import os
import time
import glob  # Papkani tozalash uchun qidiruv kutubxonasi
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# --- # BOT_TOKEN ni server sozlamalaridan qidiradi
BOT_TOKEN = os.environ.get("BOT_TOKEN", "'8934901025:AAHche8mSjOSEprTFqkkJTBfOTmDEftJIXw")
bot = TeleBot(BOT_TOKEN)

# Foydalanuvchilarning tanlagan tilini saqlash uchun lug'at
user_languages = {}

# 3 tilda xabarlar lug'ati
bot_strings = {
    'uz': {
        'welcome': "👋 Salom! **ViDore** botiga xush kelibsiz!\n\n📥 Menga YouTube, Instagram yoki TikTok videosining havolasini (link) yuboring, yuklab beraman!",
        'downloading': "⏳ ViDore videoni yuklab olmoqda, iltimos kuting...",
        'success': "✨ Video **ViDore** bot orqali muvaffaqiyatli yuklab olindi!",
        'error': "❌ Kechirasiz, bu linkdan videoni yuklab bo'lmadi.",
        'fallback': "⚠️ Iltimos, faqat to'g'ri video havolasini (linkini) yuboring!",
        'size_error': "⚠️ Kechirasiz, video hajmi juda katta ({size} MB).\nTelegram botlar bepul rejimda ko'pi bilan 50 MB gacha fayl yubora oladi."
    },
    'ru': {
        'welcome': "👋 Привет! Добро пожаловать в бот **ViDore**!\n\n📥 Отправьте мне ссылку на видео из YouTube, Instagram или TikTok, и я скачаю его для вас!",
        'downloading': "⏳ ViDore скачивает видео, пожалуйста, подождите...",
        'success': "✨ Видео успешно скачано через бот **ViDore**!",
        'error': "❌ Извините, не удалось скачать видео по этой ссылке.",
        'fallback': "⚠️ Пожалуйста, отправьте корректную ссылку на видео!" ,
        'size_error': "⚠️ Извините, размер видео слишком большой ({size} МБ).\nTelegram боты в бесплатном режиме могут отправлять файлы только до 50 МБ."
    },
    'en': {
        'welcome': "👋 Hello! Welcome to **ViDore** bot!\n\n📥 Send me a YouTube, Instagram, or TikTok video link, and I will download it for you!",
        'downloading': "⏳ ViDore is downloading the video, please wait...",
        'success': "✨ Video successfully downloaded via **ViDore** bot!",
        'error': "❌ Sorry, failed to download video from this link.",
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

# Video yuklash qismi (Asosiy funksiya)
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
    
    # Vaqtinchalik unikal fayl prefiksi
    file_prefix = f"tg_{chat_id}_{int(time.time())}"
    file_name = f"{file_prefix}.mp4"
    
    ydl_opts = {
    # Скачиваем видео не выше 480p, чтобы обойти блокировки и влезть в лимит 50 МБ
    'format': 'best[height<=480]/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    # Имитируем поведение реального браузера более детально
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,video/webm,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
    }
}

    try:
        # 1. Videoni yuklaymiz
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # 2. Agar tayyor .mp4 fayl ochilgan bo'lsa
        if os.path.exists(file_name):
            file_size_mb = os.path.getsize(file_name) / (1024 * 1024)  # MB ga o'giramiz
            
            # Telegram cheklovini tekshiramiz (50 MB)
            if file_size_mb > 50:
                err_text = bot_strings[lang]['size_error'].format(size=int(file_size_mb))
                bot.edit_message_text(err_text, chat_id, status_message.message_id)
            else:
                # Agar 50 MB dan kichik bo'lsa, foydalanuvchiga yuboramiz
                with open(file_name, 'rb') as video_file:
                    bot.send_video(chat_id, video_file, caption=bot_strings[lang]['success'], parse_mode="Markdown")
                bot.delete_message(chat_id, status_message.message_id)
        else:
            bot.edit_message_text(bot_strings[lang]['error'], chat_id, status_message.message_id)
            
    except Exception as e:
        print(f"Yuklashda xatolik: {e}")
        bot.edit_message_text(bot_strings[lang]['error'], chat_id, status_message.message_id)
        
    finally:
        # 3. TOZALASH: Har qanday vaqtinchalik faylni o'chirish (*.mp4, *.m4a, *.part)
        temporary_files = glob.glob(f"{file_prefix}.*")
        for temp_file in temporary_files:
            try:
                os.remove(temp_file)
                print(f"🗑️ Vaqtinchalik fayl butunlay o'chirildi: {temp_file}")
            except Exception as clear_error:
                print(f"O'chirishda xato: {clear_error}")

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

# Botni ishga tushirish
# Botni ishga tushirish (Render.com da uxlab qolmasligi uchun kichik hiyla)
if __name__ == "__main__":
    # Render port so'ragani uchun orqa fonda oddiy port ochib qo'yamiz
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")

    def run_dummy_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
        server.serve_forever()

    # Veb-serverni alohida potokda yoqamiz
    threading.Thread(target=run_dummy_server, daemon=True).start()

    print("🤖 Bot muvaffaqiyatli ishga tushdi...")
    bot.infinity_polling()
