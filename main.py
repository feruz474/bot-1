import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch  # Tuzatilgan kutubxona

# --- SOZLAMALAR ---
API_TOKEN = '8623290870:AAGtoR0KGz4lvK7mpO7luUFrjAAUkP-aRic'
DOWNLOAD_PATH = 'downloads'

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- TUGMALAR ---
def main_choice_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Video yuklash", callback_data=f"v_choice|{url}"),
         InlineKeyboardButton(text="🎵 Musiqa yuklash", callback_data=f"m_choice|{url}")]
    ])

def video_quality_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="720p", callback_data=f"q_720|{url}"),
         InlineKeyboardButton(text="480p", callback_data=f"q_480|{url}")],
        [InlineKeyboardButton(text="Botni guruhga qo'shish ➕", url=f"https://t.me/share/url?url=t.me/bot_usernamingiz")]
    ])

def music_effect_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Original 🔊", callback_data=f"e_normal|{url}")],
        [InlineKeyboardButton(text="Slowed 🐢", callback_data=f"e_slowed|{url}"),
         InlineKeyboardButton(text="Concert 🏟", callback_data=f"e_concert|{url}")]
    ])

# --- ASOSIY LOGIKA ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(f"Salom {message.from_user.full_name}! 👋\nMen Selena — Instagram va YouTube yuklovchi botman.\n\nHavola yuboring yoki san'atkor ismini yozing!")

@dp.message(F.text)
async def handle_message(message: types.Message):
    if "http" in message.text:
        await message.answer("Nima yuklaymiz? Tanlang:", reply_markup=main_choice_kb(message.text))
    else:
        query = message.text
        await message.answer(f"🔎 '{query}' bo'yicha qidirilmoqda...")
        try:
            # Qidiruv logikasi (httpx xatosi bermaydi)
            results = YoutubeSearch(query, max_results=3).to_dict()
            if not results:
                await message.answer("Hech narsa topilmadi 😔")
                return

            for res in results:
                video_url = f"https://www.youtube.com/watch?v={res['id']}"
                caption = f"🎵 {res['title']}\n⏱ Davomiyligi: {res['duration']}\n👁 Ko'rishlar: {res['views']}"
                await message.answer_photo(
                    photo=res['thumbnails'][0],
                    caption=caption,
                    reply_markup=main_choice_kb(video_url)
                )
        except Exception as e:
            await message.answer("Qidiruvda xatolik yuz berdi.")

# --- CALLBACKLAR (YUKLASH) ---

@dp.callback_query(F.data.startswith("v_choice"))
async def v_step(call: types.CallbackQuery):
    url = call.data.split("|")[1]
    await call.message.edit_reply_markup(reply_markup=video_quality_kb(url))

@dp.callback_query(F.data.startswith("m_choice"))
async def m_step(call: types.CallbackQuery):
    url = call.data.split("|")[1]
    await call.message.edit_reply_markup(reply_markup=music_effect_kb(url))

@dp.callback_query(F.data.startswith("q_"))
async def download_video(call: types.CallbackQuery):
    data = call.data.split("|")
    quality = data[0].split("_")[1]
    url = data[1]
    
    msg = await call.message.answer(f"📥 {quality}p yuklanmoqda...")
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': f'{DOWNLOAD_PATH}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            await call.message.answer_video(video=FSInputFile(filename), caption="Tayyor! ✅")
            os.remove(filename)
    except Exception as e:
        await call.message.answer(f"Video yuklashda xato: {e}")
    await msg.delete()

@dp.callback_query(F.data.startswith("e_"))
async def download_audio(call: types.CallbackQuery):
    data = call.data.split("|")
    effect = data[0].split("_")[1]
    url = data[1]
    
    msg = await call.message.answer(f"🎼 Musiqa ({effect}) tayyorlanmoqda...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_PATH}/%(id)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
            await call.message.answer_audio(audio=FSInputFile(filename), caption=f"Musiqa tayyor! 🎧")
            os.remove(filename)
    except Exception as e:
        await call.message.answer(f"Musiqa yuklashda xato: {e}")
    await msg.delete()

# --- ISHGA TUSHIRISH ---
async def on_startup():
    # Terminalda yashil rangli yozuv
    print("\033[92m" + "="*40)
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    print("Selena ishga tayyor...")
    print("="*40 + "\033[0m")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\033[91mBot to'xtatildi\033[0m")