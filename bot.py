import os
import yt_dlp
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔑 Bu yerga BotFather dan olgan tokeningizni qo‘ying
TOKEN = "8495068274:AAGcKkM6sakKRBDhBLL0TlxXVBAZ4-Gny9I"

# Foydalanuvchi state
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_state[chat_id] = {"link": None, "mode": None, "quality": None}
    await update.message.reply_text("👋 Salom! Video yoki MP3 yuklab olish uchun link yuboring:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    state = user_state.get(chat_id, {"link": None, "mode": None, "quality": None})

    # 1️⃣ Agar link yuborilgan bo‘lsa
    if "http" in text:
        state["link"] = text
        user_state[chat_id] = state
        keyboard = [["🎬 Video"], ["🎧 MP3"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Nimani yuklab olmoqchisiz?", reply_markup=reply_markup)
        return

    # 2️⃣ Video tanlangan bo‘lsa
    if text == "🎬 Video":
        if not state.get("link"):
            await update.message.reply_text("Iltimos, avval video link yuboring.")
            return
        state["mode"] = "video"
        user_state[chat_id] = state
        keyboard = [["360p", "720p"], ["1080p", "4K"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Video sifatini tanlang:", reply_markup=reply_markup)
        return

    # 3️⃣ MP3 tanlangan bo‘lsa
    if text == "🎧 MP3":
        if not state.get("link"):
            await update.message.reply_text("Iltimos, avval video link yuboring.")
            return
        state["mode"] = "mp3"
        user_state[chat_id] = state
        await download(update, context)
        return

    # 4️⃣ Video sifati tanlansa
    if text in ["360p", "720p", "1080p", "4K"]:
        if not state.get("link") or state.get("mode") != "video":
            await update.message.reply_text("Iltimos, avval video link yuboring va video tanlang.")
            return
        state["quality"] = text
        user_state[chat_id] = state
        await download(update, context)
        return

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    state = user_state.get(chat_id)
    url = state.get("link")
    mode = state.get("mode")
    quality = state.get("quality")

    await update.message.reply_text("⏳ Yuklanmoqda...")

    try:
        if mode == "video":
            format_map = {
                "360p": "best[height<=360]/best",
                "720p": "best[height<=720]/best",
                "1080p": "best[height<=1080]/best",
                "4K": "best[height<=2160]/best"
            }
            ydl_opts = {
                "format": format_map.get(quality, "best"),
                "outtmpl": "video.%(ext)s",
                "ffmpeg_location": r"E:\python\ffmpeg-8.1-essentials_build\bin"
            }
        else:  # MP3
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "audio.%(ext)s",
                "ffmpeg_location": r"E:\python\ffmpeg-8.1-essentials_build\bin",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)
            if mode == "mp3":
                file = os.path.splitext(file)[0] + ".mp3"

        if mode == "video":
            await update.message.reply_video(video=open(file, "rb"))
        else:
            await update.message.reply_audio(audio=open(file, "rb"))

    except Exception as e:
        await update.message.reply_text(
            f"❌ Video yoki MP3 yuklab bo‘lmadi.\nXato: {e}\nBoshqa sifatni tanlab ko‘ring."
        )

    # Faylni o‘chirish va state tozalash
    if os.path.exists(file):
        os.remove(file)
    user_state[chat_id] = {"link": None, "mode": None, "quality": None}

# Botni ishga tushirish
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
