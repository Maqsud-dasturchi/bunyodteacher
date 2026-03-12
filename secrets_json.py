"""
Maxfiy so'zlar JSON boshqaruvi moduli
Bu modul maxfiy so'zlarni JSON faylda saqlash va boshqarish uchun yaratilgan
"""

import json
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from config import ADMIN_ID

# Router yaratish
router = Router()
db = Database()

# JSON fayl nomi
SECRETS_FILE = "secrets.json"

# ========== JSON FUNKSIYALARI ==========

def load_secrets():
    """Maxfiy so'zlarni JSON fayldan yuklash"""
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('secrets', {})
        except Exception as e:
            print(f"❌ JSON faylni yuklashda xatolik: {e}")
            return {}
    return {}

def save_secrets(secrets):
    """Maxfiy so'zlarni JSON faylga saqlash"""
    try:
        data = {
            "version": "1.0.0",
            "last_updated": "2024-02-17",
            "secrets": secrets
        }
        with open(SECRETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Maxfiy so'zlar saqlandi: {SECRETS_FILE}")
        return True
    except Exception as e:
        print(f"❌ JSON faylga saqlashda xatolik: {e}")
        return False

def sync_secrets_to_db():
    """JSON dagi maxfiy so'zlarni database ga sinxronizatsiya qilish"""
    secrets = load_secrets()
    
    for teacher_name, secret_word in secrets.items():
        # Database da borligini tekshirish
        existing_secret = db.get_secret(teacher_name)
        
        if existing_secret != secret_word:
            # Database ni yangilash
            db.update_secret(teacher_name, secret_word)
            print(f"✅ {teacher_name} uchun maxfiy so'z yangilandi: {secret_word}")

# ========== MAXFIY SO'ZLAR HANDLERLARI ==========

@router.message(F.text == "🔑 Maxfiy so'zlar", F.from_user.id == ADMIN_ID)
async def manage_secrets_json(message: types.Message):
    """Maxfiy so'zlar ro'yxatini JSON dan ko'rsatish"""
    secrets = load_secrets()
    
    if not secrets:
        await message.answer(
            "🔑 <b>Maxfiy so'zlar boshqaruvi</b>\n\n"
            "❌ Hozircha hech qanday maxfiy so'z yo'q!\n\n"
            "✏️ Yangi maxfiy so'z qo'shish uchun quyidagi formatda yuboring:\n\n"
            "<code>/add_secret O'qituvchi_nomi:Maxfiy_soz</code>\n\n"
            "Masalan: <code>/add_secret O'qituvchi_nomi:yangi123</code>",
            parse_mode="HTML"
        )
        return
    
    # Ro'yxatni shakllantirish
    secrets_text = ""
    for teacher, secret in secrets.items():
        secrets_text += f"👨‍🏫 {teacher}: {secret}\n"
    
    await message.answer(
        "🔑 <b>Maxfiy so'zlar boshqaruvi (JSON)</b>\n\n"
        f"📋 <b>Joriy maxfiy so'zlar:</b>\n\n{secrets_text}\n\n"
        "✏️ <b>O'zgartirish uchun:</b>\n"
        "<code>/update_secret O'qituvchi_nomi:Yangi_maxfiy_soz</code>\n\n"
        "➕ <b>Qo'shish uchun:</b>\n"
        "<code>/add_secret O'qituvchi_nomi:Maxfiy_soz</code>\n\n"
        "🗑️ <b>O'chirish uchun:</b>\n"
        "<code>/remove_secret O'qituvchi_nomi</code>",
        parse_mode="HTML"
    )

@router.message(F.text.startswith("/add_secret"), F.from_user.id == ADMIN_ID)
async def add_secret_command(message: types.Message):
    """Yangi maxfiy so'z qo'shish"""
    try:
        parts = message.text.split(":", 1)
        if len(parts) != 2:
            await message.answer(
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "To'g'ri format:\n"
                "<code>/add_secret O'qituvchi_nomi:Maxfiy_soz</code>",
                parse_mode="HTML"
            )
            return
        
        teacher_name = parts[0].replace("/add_secret ", "").strip()
        secret_word = parts[1].strip()
        
        if not teacher_name or not secret_word:
            await message.answer("❌ O'qituvchi nomi va maxfiy so'z bo'sh bo'lmasligi kerak!", parse_mode="HTML")
            return
        
        secrets = load_secrets()
        secrets[teacher_name] = secret_word
        
        if save_secrets(secrets):
            # Database ga ham saqlash
            db.update_secret(teacher_name, secret_word)
            
            await message.answer(
                f"✅ <b>Maxfiy so'z qo'shildi!</b>\n\n"
                f"👨‍🏫 O'qituvchi: {teacher_name}\n"
                f"🔑 Maxfiy so'z: {secret_word}\n\n"
                "📊 JSON fayl va database ga saqlandi!",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Maxfiy so'zni saqlashda xatolik yuz berdi!", parse_mode="HTML")
            
    except Exception as e:
        print(f"❌ Add secret xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!", parse_mode="HTML")

@router.message(F.text.startswith("/update_secret"), F.from_user.id == ADMIN_ID)
async def update_secret_command(message: types.Message):
    """Mavjud maxfiy so'zni o'zgartirish"""
    try:
        parts = message.text.split(":", 1)
        if len(parts) != 2:
            await message.answer(
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "To'g'ri format:\n"
                "<code>/update_secret O'qituvchi_nomi:Yangi_maxfiy_soz</code>",
                parse_mode="HTML"
            )
            return
        
        teacher_name = parts[0].replace("/update_secret ", "").strip()
        new_secret = parts[1].strip()
        
        if not teacher_name or not new_secret:
            await message.answer("❌ O'qituvchi nomi va maxfiy so'z bo'sh bo'lmasligi kerak!", parse_mode="HTML")
            return
        
        secrets = load_secrets()
        
        if teacher_name not in secrets:
            await message.answer(f"❌ {teacher_name} nomli o'qituvchi topilmadi!", parse_mode="HTML")
            return
        
        old_secret = secrets[teacher_name]
        secrets[teacher_name] = new_secret
        
        if save_secrets(secrets):
            # Database ni yangilash
            db.update_secret(teacher_name, new_secret)
            
            # Barcha foydalanuvchilarga xabar yuborish
            try:
                users = db.get_all_active_users()
                success_count = 0
                error_count = 0
                
                for user in users:
                    try:
                        await message.bot.send_message(
                            user[0],  # telegram_id
                            "🔑 <b>Muhim xabar!</b>\n\n"
                            f"👨‍🏫 {teacher_name} uchun maxfiy so'z o'zgartirildi!\n\n"
                            f"🔴 Eski: {old_secret}\n"
                            f"🟢 Yangi: {new_secret}\n\n"
                            "📝 Iltimos, ro'yxatdan qayta o'ting:\n"
                            "🚀 /start\n\n"
                            "⚠️ Eski maxfiy so'z endi ishlamaydi!",
                            parse_mode="HTML"
                        )
                        success_count += 1
                    except Exception as e:
                        print(f"❌ Foydalanuvchi {user[0]} ga xabar yuborishda xatolik: {e}")
                        error_count += 1
                
                await message.answer(
                    f"✅ <b>Maxfiy so'z yangilandi!</b>\n\n"
                    f"👨‍🏫 O'qituvchi: {teacher_name}\n"
                    f"🔴 Eski: {old_secret}\n"
                    f"🟢 Yangi: {new_secret}\n\n"
                    f"📢 <b>Xabar yuborildi:</b>\n"
                    f"✅ Muvaffaqiyatli: {success_count} ta\n"
                    f"❌ Xatolik: {error_count} ta\n"
                    f"📊 Jami: {len(users)} ta foydalanuvchi",
                    parse_mode="HTML"
                )
                
            except Exception as e:
                print(f"❌ Broadcastda xatolik: {e}")
                await message.answer("⚠️ Foydalanuvchilarga xabar yuborishda xatolik yuz berdi!", parse_mode="HTML")
        else:
            await message.answer("❌ Maxfiy so'zni yangilashda xatolik yuz berdi!", parse_mode="HTML")
            
    except Exception as e:
        print(f"❌ Update secret xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!", parse_mode="HTML")

@router.message(F.text.startswith("/remove_secret"), F.from_user.id == ADMIN_ID)
async def remove_secret_command(message: types.Message):
    """Maxfiy so'zni o'chirish"""
    try:
        teacher_name = message.text.replace("/remove_secret ", "").strip()
        
        if not teacher_name:
            await message.answer(
                "❌ <b>Noto'g'ri format!</b>\n\n"
                "To'g'ri format:\n"
                "<code>/remove_secret O'qituvchi_nomi</code>",
                parse_mode="HTML"
            )
            return
        
        secrets = load_secrets()
        
        if teacher_name not in secrets:
            await message.answer(f"❌ {teacher_name} nomli o'qituvchi topilmadi!", parse_mode="HTML")
            return
        
        removed_secret = secrets.pop(teacher_name)
        
        if save_secrets(secrets):
            # Database dan o'chirish
            try:
                import sqlite3
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM teacher_secrets WHERE teacher_name = ?", (teacher_name,))
                conn.commit()
                conn.close()
                print(f"✅ {teacher_name} database dan o'chirildi")
            except Exception as e:
                print(f"❌ Database dan o'chirishda xatolik: {e}")
            
            await message.answer(
                f"✅ <b>Maxfiy so'z o'chirildi!</b>\n\n"
                f"👨‍🏫 O'qituvchi: {teacher_name}\n"
                f"🔑 Maxfiy so'z: {removed_secret}\n\n"
                "📊 JSON fayl va database dan o'chirildi!",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Maxfiy so'zni o'chirishda xatolik yuz berdi!", parse_mode="HTML")
            
    except Exception as e:
        print(f"❌ Remove secret xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!", parse_mode="HTML")

@router.message(F.text == "/sync_secrets", F.from_user.id == ADMIN_ID)
async def sync_secrets_command(message: types.Message):
    """JSON va database ni sinxronizatsiya qilish"""
    try:
        sync_secrets_to_db()
        await message.answer(
            "✅ <b>Sinxronizatsiya yakunlandi!</b>\n\n"
            "📊 JSON fayl va database sinxronizatsiya qilindi!",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"❌ Sync xatolik: {e}")
        await message.answer("❌ Sinxronizatsiyada xatolik yuz berdi!", parse_mode="HTML")

# Router ni qaytarish
def get_secrets_json_router():
    """JSON maxfiy so'zlar router ini qaytarish"""
    return router
