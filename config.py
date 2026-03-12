# Bot sozlamalari
import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Environment variables'dan olish
BOT_TOKEN = os.getenv("BOT_TOKEN", "8479744985:AAFUCKSUrxzQ8rUWO2WcLnrop_mWqN4KOPo")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5964436818"))  # Asosiy admin (eski uchun moslik)
ADMINS = [int(id.strip()) for id in os.getenv("ADMINS", "5964436818").split(",")]  # Ko'p adminlar
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003534326655"))
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/english_with_Shamsiddinov")

# Instagram sozlamalari
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://www.instagram.com/edustar_uz/")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "edustar_uz")
INSTAGRAM_REQUIRED = os.getenv("INSTAGRAM_REQUIRED", "true").lower() == "true"

# Darslar
TOTAL_LESSONS = int(os.getenv("TOTAL_LESSONS", "48"))
LESSONS_PER_PAGE = int(os.getenv("LESSONS_PER_PAGE", "12"))
TOTAL_PAGES = (TOTAL_LESSONS + LESSONS_PER_PAGE - 1) // LESSONS_PER_PAGE

# Ro'yxatdan o'tish ma'lumotlari
TEACHERS = [
    "Bunyod Shamsiddinov"
]

DAYS = [
    "Dushanba-Chorshanba-Juma",
    "Seshanba-Payshanba-Shanba"
]

# Ustozlar uchun maxfiy so'zlar (Boshlang'ich)
DEFAULT_TEACHER_SECRETS = {
    "Bunyod Shamsiddinov": "b2024"
}

# O'qituvchilar kanallari
TEACHER_CHANNELS = {
    "Bunyod Shamsiddinov": -1003887247702
}

# O'qituvchi kanallari (Chat ID -> O'qituvchi)
# Default biriktirilgan kanallar
# ESLATMA: Bu yerga haqiqiy kanal ID laringizni yozing!
TEACHER_CHANNELS_CHAT_ID = {
    -1003887247702: "Bunyod Shamsiddinov"  # Bunyod uchun kanal ID
}

# Asosiy kanal (Bunyod Shamsiddinov uchun)
MAIN_CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003887247702"))

# Content turlari
CONTENT_TYPES = {
    "listening": {"name": "🎧 Listening", "emoji": "🎧"},
    "reading": {"name": "📖 Reading", "emoji": "📖"},
    "grammar": {"name": "📚 Grammar", "emoji": "📚"},
    "vocabulary": {"name": "📝 Vocabulary", "emoji": "📝"},
    "quiz": {"name": "🧪 Quiz", "emoji": "🧪"}
}