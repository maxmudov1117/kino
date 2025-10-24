import telebot
from telebot import types
import json
import os

# Bot tokenini kiriting (BotFather'dan olingan)
BOT_TOKEN = '7283841176:AAGBPDzbX36gQSshoASmmWJsbB8cn3FXwn8'

bot = telebot.TeleBot(BOT_TOKEN)

# Kinolar ma'lumotlar bazasi - JSON faylda saqlanadi
MOVIES_FILE = 'movies_data.json'

# Dastlabki kinolar bazasi
default_movies = {
    'KN001': {
        'title': 'Titanik',
        'year': '1997',
        'genre': 'Drama, Romantika',
        'description': 'Kemada sodir bo\'lgan sevgi va fojia haqida',
        'file_id': None,  # Telegram file_id
        'file_url': None  # Yoki URL
    },
    'KN002': {
        'title': 'Avatar',
        'year': '2009',
        'genre': 'Fantastika, Sarguzasht',
        'description': 'Pandora sayyorasidagi hayot haqida',
        'file_id': None,
        'file_url': None
    }
}


# JSON fayldan kinolarni yuklash
def load_movies():
    if os.path.exists(MOVIES_FILE):
        with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Agar fayl yo'q bo'lsa, dastlabki bazani yaratish
        save_movies(default_movies)
        return default_movies


# JSON faylga kinolarni saqlash
def save_movies(movies):
    with open(MOVIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)


# Kinolar bazasini yuklash
movies_db = load_movies()

# Admin foydalanuvchi ID (o'zingizning Telegram ID)
ADMIN_ID = 5922081119  # Bu yerga o'z ID ni kiriting


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🎬 Kino Botga xush kelibsiz!

Kino kodini kiriting va men sizga kinoni topib beraman.

Masalan: KN001

📋 Buyruqlar:
/list - Barcha kinolar ro'yxati
/help - Yordam
    """

    # Admin uchun qo'shimcha ma'lumot
    if message.from_user.id == ADMIN_ID:
        welcome_text += "\n👨‍💼 Admin buyruqlari:\n/addmovie - Kino qo'shish"

    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📖 Yordam:

1️⃣ Kino kodini kiriting (masalan: KN001)
2️⃣ Men sizga kino ma'lumotlarini ko'rsataman
3️⃣ "Yuklab olish" tugmasini bosing

🔍 /list - Barcha kinolar ro'yxati
    """
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['list'])
def list_movies(message):
    if not movies_db:
        bot.reply_to(message, "❌ Hozircha kinolar bazasi bo'sh")
        return

    list_text = "📽 Mavjud kinolar ro'yxati:\n\n"
    for code, movie in movies_db.items():
        status = "✅" if (movie.get('file_id') or movie.get('file_url')) else "⏳"
        list_text += f"{status} {code} - {movie['title']} ({movie['year']})\n"

    list_text += "\n✅ - Mavjud\n⏳ - Fayl yuklanmagan"
    bot.reply_to(message, list_text)


# ADMIN: Kino qo'shish (faqat admin uchun)
@bot.message_handler(commands=['addmovie'])
def add_movie_start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu buyruq faqat admin uchun")
        return

    msg = bot.reply_to(message, """
📝 Yangi kino qo'shish:

Quyidagi formatda ma'lumot yuboring:

KOD|NOM|YIL|JANR|TAVSIF

Masalan:
KN005|Spider-Man|2002|Action, Adventure|Peter Parker haqida

Keyin video faylni yuboring.
    """)
    bot.register_next_step_handler(msg, process_movie_info)


def process_movie_info(message):
    try:
        parts = message.text.split('|')
        if len(parts) != 5:
            bot.reply_to(message, "❌ Noto'g'ri format! Qaytadan urinib ko'ring: /addmovie")
            return

        code, title, year, genre, desc = [p.strip() for p in parts]

        # Vaqtinchalik saqlash
        temp_data = {
            'code': code,
            'title': title,
            'year': year,
            'genre': genre,
            'description': desc
        }

        msg = bot.reply_to(message, f"✅ Ma'lumotlar saqlandi!\n\nEndi '{title}' uchun video faylni yuboring:")
        bot.register_next_step_handler(msg, lambda m: process_movie_file(m, temp_data))

    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")


def process_movie_file(message, temp_data):
    if message.content_type == 'video':
        file_id = message.video.file_id

        # Kinoni bazaga qo'shish
        movies_db[temp_data['code']] = {
            'title': temp_data['title'],
            'year': temp_data['year'],
            'genre': temp_data['genre'],
            'description': temp_data['description'],
            'file_id': file_id,
            'file_url': None
        }

        # JSON faylga saqlash
        save_movies(movies_db)

        bot.reply_to(message, f"""
✅ Kino muvaffaqiyatli qo'shildi!

🎬 {temp_data['title']}
🔢 Kod: {temp_data['code']}
📁 File ID: {file_id[:20]}...

Foydalanuvchilar endi bu kinoni ko'rishlari mumkin!
        """)
    else:
        bot.reply_to(message, "❌ Iltimos, video fayl yuboring!")


# Foydalanuvchi kod kiritganda
@bot.message_handler(func=lambda message: True)
def handle_code(message):
    code = message.text.strip().upper()

    if code in movies_db:
        movie = movies_db[code]

        # Kino ma'lumotlari
        movie_info = f"""
🎬 Kino topildi!

📌 Nomi: {movie['title']}
📅 Yili: {movie['year']}
🎭 Janr: {movie['genre']}
📝 Tavsif: {movie['description']}
🔢 Kod: {code}
        """

        # Agar fayl mavjud bo'lsa
        if movie.get('file_id') or movie.get('file_url'):
            markup = types.InlineKeyboardMarkup()
            download_btn = types.InlineKeyboardButton(
                "📥 Kinoni yuklab olish",
                callback_data=f"download_{code}"
            )
            markup.add(download_btn)
            bot.send_message(message.chat.id, movie_info, reply_markup=markup)
        else:
            movie_info += "\n\n⚠️ Video hali yuklanmagan."
            bot.send_message(message.chat.id, movie_info)
    else:
        error_text = f"""
❌ Kod topilmadi: {code}

Mavjud kodlar ro'yxatini ko'rish uchun /list ni yuboring.
        """
        bot.reply_to(message, error_text)


@bot.callback_query_handler(func=lambda call: call.data.startswith('download_'))
def handle_download(call):
    code = call.data.split('_')[1]

    if code in movies_db:
        movie = movies_db[code]

        bot.answer_callback_query(call.id, "Yuklab olinmoqda...")

        # Telegram'dagi videoni yuborish
        if movie.get('file_id'):
            try:
                bot.send_video(
                    call.message.chat.id,
                    movie['file_id'],
                    caption=f"🎬 {movie['title']} ({movie['year']})"
                )
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Video yuborishda xatolik: {str(e)}")

        # Yoki URL orqali yuborish
        elif movie.get('file_url'):
            bot.send_message(
                call.message.chat.id,
                f"🔗 Yuklab olish havolasi:\n{movie['file_url']}"
            )
        else:
            bot.send_message(call.message.chat.id, "❌ Video fayl topilmadi")
    else:
        bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi", show_alert=True)


# Botni ishga tushirish
if __name__ == '__main__':
    print("Bot ishga tushdi...")
    print(f"Kinolar soni: {len(movies_db)}")
    bot.polling(none_stop=True)