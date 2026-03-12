from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_URL, INSTAGRAM_URL, TEACHERS, DAYS

class Keyboards:
    @staticmethod
    def start_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="🚀 Boshlash")
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📚 Darsliklar")
        builder.button(text="ℹ️ Biz haqimizda")
        builder.adjust(1, 1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def user_menu() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📚 Darslar")
        builder.button(text="🔄 Malumotlarni tozalash")
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def admin_menu() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="👥 Barcha foydalanuvchilar")
        builder.button(text="📢 Barchaga xabar yuborish")
        builder.button(text="🚫 Bloklash")
        builder.button(text="✅ Blokdan chiqarish")
        builder.button(text="📋 Kontentlar")
        builder.adjust(2, 2, 1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def contact_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📱 Raqamni yuborish", request_contact=True)
        builder.button(text="❌ Bekor qilish")
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def days_keyboard() -> InlineKeyboardMarkup:
        from config import DAYS
        builder = InlineKeyboardBuilder()
        
        for i, day in enumerate(DAYS):
            builder.button(text=day, callback_data=f"day_{i}")
        
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def lessons_pagination(page=1) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        # 48 dars, har sahifada 6 ta
        total_pages = 8
        start = (page - 1) * 6 + 1
        end = min(page * 6, 48)
        
        # Dars tugmalari
        for i in range(start, end + 1):
            builder.button(text=f"Dars {i}", callback_data=f"lesson_{i}")
        
        # Sahifa navigatsiyasi
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page_{page+1}"))
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.adjust(3)
        return builder.as_markup()
    
    @staticmethod
    def lesson_menu(lesson_num) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        content_types = [
            ("🎧 Listening", "listening"),
            ("📖 Reading", "reading"),
            ("📝 Grammar", "grammar"),
            ("📚 Vocabulary", "vocabulary")
        ]
        
        for text, content_type in content_types:
            builder.button(text=text, callback_data=f"type_{lesson_num}_{content_type}")
        
        builder.adjust(2)
        
        # Orqaga qaytish tugmasi
        builder.button(text="⬅️ Orqaga", callback_data="back_to_lessons")
        
        return builder.as_markup()
    
    @staticmethod
    def content_parts(lesson_num, content_type, content_parts) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        
        # Boshqa content types uchun eski kod
        for i, part in enumerate(content_parts):
            hashtag = part[1]  # hashtag (index 1, not 0)
            file_type = part[4]  # file_type (index 4, not 3)
            
            # Ikonka tanlash
            if file_type == "photo":
                icon = "🖼️"
            elif file_type == "audio":
                icon = "🎧"
            elif file_type == "video":
                icon = "🎥"
            elif file_type == "document":
                icon = "📄"
            else:
                icon = "📝"
            
            # Hashtag'dan raqamni olish
            import re
            match = re.search(r'(\d+)', hashtag)
            if match:
                part_num = match.group(1)
                button_text = f"{icon} {content_type.title()} {part_num}"
                builder.button(text=button_text, callback_data=f"content_{hashtag}")
            else:
                button_text = f"{icon} {content_type.title()}"
                builder.button(text=button_text, callback_data=f"content_{hashtag}")
        
        builder.adjust(2)
        
        # Orqaga qaytish tugmasi
        builder.button(text="⬅️ Orqaga", callback_data="back_to_lessons")
        
        return builder.as_markup()
    
    @staticmethod
    def instagram_check(instagram_url) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📷 Instagramga o'tish", url=instagram_url)
        builder.button(text="✅ Tekshirish", callback_data="check_instagram")
        builder.button(text="⏭️ Keyinroq", callback_data="skip_instagram")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def cancel_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="❌ Bekor qilish")
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def confirm_clear_data() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="✅ Ha, to'liq tozalash")
        builder.button(text="❌ Yo'q, bekor qilish")
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def users_management_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Barcha foydalanuvchilar", callback_data="excel_all_users")
        builder.button(text="👥 Guruhlar bo'yicha", callback_data="excel_by_groups")
        builder.button(text="⬅️ Orqaga", callback_data="admin_back")
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def subscription_check() -> InlineKeyboardMarkup:
        """Obuna tekshirish tugmalari"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Telegram kanal", url=CHANNEL_URL)
        builder.button(text="📷 Instagram", url=INSTAGRAM_URL)
        builder.button(text="✅ Obuna bo'ldim", callback_data="check_both_subscriptions")
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def back_to_lessons() -> InlineKeyboardMarkup:
        """Orqaga darslar menugasiga qaytish tugmasi"""
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Orqaga darslarga", callback_data="back_to_lessons")
        return builder.as_markup()

# InlineKeyboardBuilder import qilish
from aiogram.utils.keyboard import InlineKeyboardBuilder

kb = Keyboards()
