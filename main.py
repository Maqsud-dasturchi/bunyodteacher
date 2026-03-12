import asyncio
import logging
import pandas as pd
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, ADMIN_ID, ADMINS, CHANNEL_ID, CHANNEL_URL, INSTAGRAM_URL, INSTAGRAM_REQUIRED, TEACHERS
from database import db
from keyboards import kb
from states import Registration, AdminState

# Botni yaratish
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Maxfiy so'zlar JSON handlerini import qilish
from secrets_json import get_secrets_json_router, sync_secrets_to_db

# Router'lar ro'yxatdan o'tkazish
dp.include_router(get_secrets_json_router())
from middleware import BlockingMiddleware
dp.message.middleware(BlockingMiddleware())
dp.callback_query.middleware(BlockingMiddleware())

# ========== UNIVERSAL BEKOR QILISH HANDLER ==========
@dp.message(F.text == "❌ Bekor qilish")
async def universal_cancel_handler(message: types.Message, state: FSMContext):
    """Barcha state lar uchun universal bekor qilish"""
    current_state = await state.get_state()
    user_id = message.from_user.id
    
    print(f"❌ Foydalanuvchi {user_id} {current_state} holatida bekor qilmoqda")
    
    await state.clear()
    
    if user_id == ADMIN_ID:
        await message.answer(
            "❌ <b>Amal bekor qilindi!</b>\n\nAdmin paneliga qaytdingiz.",
            reply_markup=kb.admin_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Amal bekor qilindi!</b>\n\nAsosiy menyu.",
            reply_markup=kb.user_menu(),
            parse_mode="HTML"
        )

# ========== YORDAMCHI FUNKSIYALAR ==========

def is_admin(user_id):
    """Admin ekanligini tekshirish - ko'p adminlar uchun"""
    return user_id in ADMINS

def extract_file_info(message):
    """Fayl ma'lumotlarini olish"""
    if message.audio:
        return message.audio.file_id, "audio"
    elif message.document:
        return message.document.file_id, "document"
    elif message.video:
        return message.video.file_id, "video"
    elif message.voice:
        return message.voice.file_id, "voice"
    elif message.photo:
        return message.photo[-1].file_id, "photo"
    elif message.text:
        return message.text, "text"
    return None, None

# ========== OBUNA TEKSHIRUVI ==========
async def is_subscribed(user_id):
    """Foydalanuvchining kanalga obuna bo'lganligini tekshirish"""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Kanal tekshirish xato: {e}")
        # If bot is not admin, consider all users subscribed
        print(f"⚠️ Bot kanalga admin emas, barcha foydalanuvchilarni obuna deb hisoblaymiz")
        return True

# ========== KANALNI ESHITISH ==========
# Bu handler o'chirildi — pastda (line ~1132) asosiy handler ishlatiladi

# ========== BLOKLASH FUNKSIYALARI ==========
@dp.message(F.text == "🚫 Bloklash", F.from_user.id.in_(ADMINS))
async def block_user_start(message: types.Message, state: FSMContext):
    """Foydalanuvchini bloklashni boshlash"""
    await message.answer(
        "🚫 <b>Foydalanuvchini bloklash</b>\n\n"
        "📝 <b>Bloklaydigan foydalanuvchining Telegram ID sini kiriting:</b>\n\n"
        "💡 <i>Foydalanuvchi ID sini /debug buyrug'i orqali topishingiz mumkin</i>\n"
        "➡️ <i>Bekor qilish uchun '❌ Bekor qilish' deb yozing</i>",
        reply_markup=kb.cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminState.waiting_block_reason)

@dp.message(AdminState.waiting_block_reason)
async def block_user_input(message: types.Message, state: FSMContext):
    """Foydalanuvchi ID sini qabul qilish va bloklash"""
    try:
        user_id = int(message.text.strip())
        
        # O'zini bloklashga ruxsat berilmaydi
        if user_id == ADMIN_ID:
            await message.answer("❌ O'zingizni bloklay olmaysiz!", reply_markup=kb.admin_menu())
            await state.clear()
            return
        
        # Foydalanuvchi borligini tekshirish
        user = db.get_user(user_id)
        if not user:
            await message.answer("❌ Bunday ID li foydalanuvchi topilmadi!", reply_markup=kb.admin_menu())
            await state.clear()
            return
        
        # Sabab so'rash
        await state.update_data(block_user_id=user_id)
        await message.answer(
            f"👤 <b>Foydalanuvchi:</b> {user[1]}\n"
            f"🆔 <b>ID:</b> {user_id}\n\n"
            "📝 <b>Bloklash sababini kiriting:</b>\n\n"
            "➡️ <i>Bekor qilish uchun '❌ Bekor qilish' deb yozing</i>",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AdminState.waiting_block_confirmation)
        
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! Faqat raqam kiriting:", reply_markup=kb.cancel_keyboard())

@dp.message(AdminState.waiting_block_confirmation)
async def block_user_confirm(message: types.Message, state: FSMContext):
    """Foydalanuvchini bloklashni tasdiqlash"""
    data = await state.get_data()
    user_id = data.get('block_user_id')
    reason = message.text.strip()
    
    if not reason:
        await message.answer("❌ Sababni kiriting!", reply_markup=kb.cancel_keyboard())
        return
    
    try:
        # Foydalanuvchini bloklash
        success = db.block_user(user_id, reason, ADMIN_ID)
        
        if success:
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    user_id,
                    "⛔️ <b>Siz admin tomonidan bloklandingiz!</b>\n\n"
                    f"📝 Sabab: {reason}\n\n"
                    "📞 Admin bilan bog'lanish uchun:\n"
                    f"🆔 Admin ID: {ADMIN_ID}",
                    parse_mode="HTML"
                )
            except:
                pass  # Foydalanuvchi botni bloklagan bo'lishi mumkin
            
            # Foydalanuvchi ma'lumotlarini olish
            user = db.get_user(user_id)
            user_name = user[1] if user else "Noma'lum"
            
            await message.answer(
                f"✅ <b>Foydalanuvchi bloklandi!</b>\n\n"
                f"👤 Ism: {user_name}\n"
                f"🆔 ID: {user_id}\n"
                f"📝 Sabab: {reason}\n\n"
                "🗑️ Barcha ma'lumotlar o'chirildi va botdan foydalanishi taqiqlandi!",
                reply_markup=kb.admin_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi!", reply_markup=kb.admin_menu())
        
        await state.clear()
        
    except Exception as e:
        print(f"❌ Bloklashda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=kb.admin_menu())
        await state.clear()

@dp.message(F.text == "✅ Blokdan chiqarish", F.from_user.id.in_(ADMINS))
async def unblock_user_start(message: types.Message, state: FSMContext):
    """Foydalanuvchini blokdan chiqarishni boshlash"""
    await message.answer(
        "✅ <b>Foydalanuvchini blokdan chiqarish</b>\n\n"
        "📝 <b>Blokdan chiqaradigan foydalanuvchining Telegram ID sini kiriting:</b>\n\n"
        "💡 <i>Foydalanuvchi ID sini /debug buyrug'i orqali topishingiz mumkin</i>\n"
        "➡️ <i>Bekor qilish uchun '❌ Bekor qilish' deb yozing</i>",
        reply_markup=kb.cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminState.waiting_unblock_id)

@dp.message(AdminState.waiting_unblock_id)
async def unblock_user_input(message: types.Message, state: FSMContext):
    """Foydalanuvchi ID sini qabul qilish va blokdan chiqarish"""
    try:
        user_id = int(message.text.strip())
        
        # Foydalanuvchi borligini tekshirish
        user = db.get_user(user_id)
        if not user:
            await message.answer("❌ Bunday ID li foydalanuvchi topilmadi!", reply_markup=kb.admin_menu())
            await state.clear()
            return
        
        # Bloklanganligini tekshirish
        if not db.is_user_blocked(user_id):
            await message.answer("❌ Bu foydalanuvchi bloklanmagan!", reply_markup=kb.admin_menu())
            await state.clear()
            return
        
        # Blokdan chiqarish
        success = db.unblock_user(user_id)
        
        if success:
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    user_id,
                    "✅ <b>Siz blokdan chiqarildingiz!</b>\n\n"
                    "🎉 Botdan qayta foydalanishingiz mumkin!\n"
                    "📚 Ro'yxatdan qayta o'ting: /start",
                    parse_mode="HTML"
                )
            except:
                pass
            
            # Tiklangan foydalanuvchi ma'lumotlarini olish
            user = db.get_user(user_id)
            user_name = user[1] if user else "Blokdan chiqarilgan foydalanuvchi"
            
            await message.answer(
                f"✅ <b>Foydalanuvchi blokdan chiqarildi!</b>\n\n"
                f"👤 Ism: {user_name}\n"
                f"🆔 ID: {user_id}\n\n"
                "🎉 Botdan qayta foydalanishi mumkin!",
                reply_markup=kb.admin_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Bu foydalanuvchi bloklanmagan yoki topilmadi!", reply_markup=kb.admin_menu())
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! Faqat raqam kiriting:", reply_markup=kb.cancel_keyboard())
    except Exception as e:
        print(f"❌ Blokdan chiqarishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=kb.admin_menu())
        await state.clear()

# ========== EXCEL EXPORT COMMAND ==========
@dp.message(Command("excel_users"), F.from_user.id.in_(ADMINS))
async def excel_users_command(message: types.Message):
    """Foydalanuvchilarni Excel faylga chiqarish"""
    print("🔍 /excel_users buyrug'i yuborildi")
    
    try:
        # Database dan ma'lumot olish
        users = db.get_all_users_for_excel()
        
        print(f"📊 {len(users)} ta foydalanuvchi topildi")
        
        if not users:
            await message.answer("❌ Foydalanuvchilar topilmadi!", reply_markup=kb.admin_menu())
            return
        
        # DataFrame yaratish
        df = pd.DataFrame(users, columns=[
            'Telegram ID', 'Ism Familiya', 'Telefon', 'Guruh', 
            'Instagram Obunasi', 'Instagram Username', 'Status'
        ])
        
        # Fayl nomi
        filename = f"barcha_foydalanuvchilar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        import os
        filepath = os.path.join(os.getcwd(), filename)
        
        # Excel faylni saqlash
        df.to_excel(filepath, index=False)
        print(f"✅ Excel fayl yaratildi: {filename}")
        
        # Faylni yuborish
        await message.answer_document(
            FSInputFile(filepath),
            caption=f"📊 <b>Barcha foydalanuvchilar ro'yxati (Excel)</b>\n\n"
                   f"👥 Jami foydalanuvchilar: {len(users)} ta\n"
                   f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                   f"📋 Excel faylda to'liq ma'lumotlar mavjud!",
            parse_mode="HTML"
        )
        
        # Faylni o'chirish
        import os
        os.remove(filepath)
        
        print(f"✅ {len(users)} ta foydalanuvchi Excel fayli yuborildi!")
        
    except Exception as e:
        print(f"❌ XATOLIK: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)[:50]}", reply_markup=kb.admin_menu())

# ========== DEBUG KOMANDASI ==========
@dp.message(Command("debug"))
async def debug_command(message: types.Message):
    """Debug uchun buyruq"""
    if not is_admin(message.from_user.id):
        return
    
    # Bazadagi barcha kontent
    all_content = db.debug_content()
    
    if not all_content:
        await message.answer("📭 Bazada kontent yo'q")
        return
    
    text = "📁 BAZADAGI BARCHA KONTENT:\n\n"
    
    for item in all_content:
        hashtag, ctype, file_id, ftype, msg_id, saved_at = item
        text += f"🏷️ {hashtag}\n"
        text += f"   📂 Turi: {ctype}\n"
        text += f"   📄 Fayl turi: {ftype}\n"
        text += f"   ⏰ Saqlangan: {saved_at}\n\n"
    
    await message.answer(text)

# ========== START VA RO'YXATDAN O'TISH ==========
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Bloklanganligini tekshirish
    if db.is_user_blocked(message.from_user.id):
        await message.answer("⛔️ Kechirasiz, siz admin tomonidan bloklangansiz.")
        return
    
    # Admin bo'lsa
    if is_admin(message.from_user.id):
        await message.answer(
            "👑 <b>Admin Paneliga Xush Kelibsiz!</b>\n\n"
            "🎯 Barcha funksiyalar siz uchun ochiq\n"
            "📊 Statistika va boshqaruv\n"
            "📢 Broadcast xabarlar\n"
            "🚫 Foydalanuvchilar boshqaruvi",
            reply_markup=kb.admin_menu(),
            parse_mode="HTML"
        )
        return
    
    # Ro'yxatdan o'tganligini tekshirish
    if db.is_user_registered(message.from_user.id):
        # Obuna holatini tekshirish
        subscribed = await is_subscribed(message.from_user.id)
        
        if subscribed:
            # Agar ro'yxatdan o'tgan va obuna bo'lsa, to'g'ridan-to'g'ri asosiy menyu
            await message.answer(
                "🌟 <b>Asosiy menyu</b>\n\n"
                "📚 Darslarni o'rganish",
                reply_markup=kb.user_menu(),
                parse_mode="HTML"
            )
        else:
            # Agar obuna bo'lmasa, obuna tugmalarini ko'rsatish
            await message.answer(
                "🔐 <b>Botdan foydalanish uchun obuna talab qilinadi</b>\n\n"
                "📢 <b>Telegram kanalga obuna bo'ling</b>\n"
                "📷 <b>Instagramga obuna bo'ling</b>\n\n"
                "✅ Obuna bo'lgandan so'ng 'Obuna bo'ldim' tugmasini bosing!",
                reply_markup=kb.subscription_check(),
                parse_mode="HTML"
            )
    else:
        # Agar ro'yxatdan o'tmagan bo'lsa, obuna tugmalari bilan ro'yxatdan o'tish
        await message.answer(
            "🎓 <b>Edu Star Bot ga xush kelibsiz!</b>\n\n"
            "� <b>Botdan foydalanish uchun obuna talab qilinadi</b>\n\n"
            "📢 <b>Telegram kanalga obuna bo'ling</b>\n"
            "📷 <b>Instagramga obuna bo'ling</b>\n\n"
            "✅ Obuna bo'lgandan so'ng 'Obuna bo'ldim' tugmasini bosing!\n\n"
            "� <b>Keyin ro'yxatdan o'tish uchun ism va familiyangizni kiriting:</b>",
            reply_markup=kb.subscription_check(),
            parse_mode="HTML"
        )
        await state.set_state(Registration.full_name)

@dp.message(F.text == "🔄 Malumotlarni tozalash")
async def update_user_info(message: types.Message, state: FSMContext):
    """Foydalanuvchi ma'lumotlarini to'liq tozalash"""
    user_id = message.from_user.id
    
    print(f"🔄 Foydalanuvchi {user_id} ma'lumotlarini tozalashni so'radi")
    
    # Foydalanuvchi ma'lumotlarini tekshirish
    user_info = db.get_user(user_id)
    
    # Agar ro'yxatdan o'tmagan bo'lsa
    if not user_info:
        await message.answer(
            "❌ Siz ro'yxatdan o'tmagansiz!\n\n"
            "📝 Iltimos, /start buyrug'i bilan ro'yxatdan o'ting.",
            reply_markup=kb.start_keyboard()
        )
        return
    
    # Tasdiqlash so'rash
    await message.answer(
        "⚠️ <b>Diqqat!</b>\n\n"
        "Sizning barcha ma'lumotlaringiz bazadan o'chiriladi:\n"
        "• Ro'yxatdan o'tish ma'lumotlari\n"
        "• Instagram obuna ma'lumotlari\n\n"
        "Qaytadan ro'yxatdan o'tishingiz kerak bo'ladi.\n\n"
        "Davom etishni hohlaysizmi?",
        reply_markup=kb.confirm_clear_data(),
        parse_mode="HTML"
    )

@dp.message(F.text == "✅ Ha, to'liq tozalash")
async def confirm_clear_data_message(message: types.Message, state: FSMContext):
    """Malumotlarni to'liq tozalashni tasdiqlash (message handler)"""
    user_id = message.from_user.id
    
    print(f"✅ Foydalanuvchi {user_id} ma'lumotlarini tozalashni tasdiqladi")
    
    try:
        # Foydalanuvchiga jarayon boshlanganligi haqida xabar
        await message.answer("⏳ Ma'lumotlaringiz tozalanmoqda...")
        
        # Barcha ma'lumotlarni o'chirish
        db.delete_user(user_id)
        
        # State ni tozalash
        await state.clear()
        
        # Muvaffaqiyatli xabari
        await message.answer(
            "✅ <b>Barcha ma'lumotlaringiz muvaffaqiyatli o'chirildi!</b>\n\n"
            "📝 <b>Iltimos, qaytadan ro'yxatdan o'ting:</b>\n\n"
            "🎓 Ism va familiyangizni kiriting:",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="HTML"
        )
        
        # Ro'yxatdan o'tishni boshlash
        await state.set_state(Registration.full_name)
        
    except Exception as e:
        print(f"❌ Ma'lumotlarni tozalashda xatolik: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi! Iltimos, admin ga murojaat qiling.",
            reply_markup=kb.user_menu()
        )
        await state.clear()

@dp.message(F.text == "❌ Yo'q, bekor qilish")
async def cancel_clear_data_message(message: types.Message, state: FSMContext):
    """Malumotlarni tozalashni bekor qilish (message handler)"""
    user_id = message.from_user.id
    
    print(f"❌ Foydalanuvchi {user_id} ma'lumotlarni tozalashni bekor qildi")
    
    await state.clear()
    await message.answer(
        "✅ <b>Amal bekor qilindi!</b>\n\n"
        "🏠 Bosh menyu:",
        reply_markup=kb.user_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "confirm_update")
async def confirm_update_info(call: types.CallbackQuery, state: FSMContext):
    """Malumotlarni to'liq tozalashni tasdiqlash"""
    user_id = call.from_user.id
    
    print(f"✅ Foydalanuvchi {user_id} ma'lumotlarini tozalashni tasdiqladi")
    
    try:
        # Foydalanuvchiga jarayon boshlanganligi haqida xabar
        await call.message.edit_text(
            "⏳ <b>Ma'lumotlarni tozalash boshlandi...</b>\n\n"
            "Iltimos, biroz kuting.",
            parse_mode="HTML"
        )
        
        # Foydalanuvchi ma'lumotlarini bazadan o'chirish
        success = db.delete_user(user_id)
        
        if success:
            print(f"✅ Foydalanuvchi {user_id} ma'lumotlari muvaffaqiyatli o'chirildi")
            
            # Muvaffaqiyatli xabar
            await call.message.edit_text(
                "✅ <b>Ma'lumotlar to'liq to'landi!</b>\n\n"
                "🗑️ Barcha ma'lumotlaringiz bazadan o'chirildi:\n"
                "• Ro'yxatdan o'tish ma'lumotlari\n"
                "• Instagram obuna ma'lumotlari\n\n"
                "🔄 Endi qaytadan ro'yxatdan o'tishingiz kerak.",
                parse_mode="HTML"
            )
            
            # Ro'yxatdan o'tishni boshlash - to'g'ridan-to'g'ri ism so'rash
            await call.message.answer(
                "🎓 <b>Edu Star Bot ga qayta xush kelibsiz!</b>\n\n"
                "📝 Ro'yxatdan o'tish uchun ism va familiyangizni kiriting:",
                parse_mode="HTML"
            )
            
            # State ni tozalash va ro'yxatdan o'tishni boshlash
            await state.clear()
            await state.set_state(Registration.full_name)
            
        else:
            print(f"❌ Foydalanuvchi {user_id} ma'lumotlarini o'chirib bo'lmadi")
            await call.message.edit_text(
                "❌ <b>Xatolik yuz berdi!</b>\n\n"
                "Ma'lumotlarni o'chirib bo'lmadi.\n"
                "Iltimos, admin bilan bog'laning:\n"
                f"👤 Admin ID: {ADMIN_ID}",
                parse_mode="HTML"
            )
        
    except Exception as e:
        print(f"❌ Foydalanuvchi {user_id} ma'lumotlarini o'chirishda xatolik: {e}")
        await call.message.edit_text(
            f"❌ <b>Xatolik yuz berdi!</b>\n\n"
            f"Xatolik: {str(e)[:100]}...\n\n"
            "Iltimos, admin bilan bog'laning.",
            parse_mode="HTML"
        )

@dp.callback_query(F.data == "cancel_update")
async def cancel_update_info(call: types.CallbackQuery):
    """Malumotlarni to'liq tozalashni bekor qilish"""
    user_id = call.from_user.id
    
    print(f"❌ Foydalanuvchi {user_id} ma'lumotlarini tozalashni bekor qildi")
    
    await call.message.edit_text(
        "❌ <b>Bekor qilindi!</b>\n\n"
        "Sizning ma'lumotlaringiz o'zgarishsiz qoldi.",
        parse_mode="HTML"
    )

# Ro'yxatdan o'tish bosqichlari
@dp.message(Registration.full_name)
async def get_name(message: types.Message, state: FSMContext):
    """Ismni olish"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Ism kamida 2 harfdan iborat bo'lishi kerak!")
        return
    
    await state.update_data(full_name=name)
    await message.answer(
        f"✅ <b>Ism qabul qilindi:</b> {name}\n\n"
        "📱 <b>Telefon raqamingizni yuboring:</b>\n\n"
        "👉 Raqamni yuborish tugmasini bosing yoki raqamni kiriting:",
        reply_markup=kb.contact_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.phone)

@dp.message(Registration.phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    # Avtomatik ravishda Bunyod Shamsiddinovni o'qituvchi sifatida belgilash
    await state.update_data(teacher="Bunyod Shamsiddinov")
    await message.answer("Dars kunlarini tanlang:", reply_markup=kb.days_keyboard())
    await state.set_state(Registration.days)

@dp.callback_query(Registration.days, F.data.startswith("day_"))
async def get_days(call: types.CallbackQuery, state: FSMContext):
    from config import DAYS
    index = int(call.data.split("_")[1])
    days = DAYS[index]
    
    await state.update_data(days=days)
    await call.message.answer("Dars vaqtini kiriting (masalan: 14:00):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.time)

@dp.message(Registration.time)
async def get_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("🔒 Maxfiy so'zni kiriting:")
    await state.set_state(Registration.secret_word)

@dp.message(Registration.secret_word)
async def check_secret_word(message: types.Message, state: FSMContext):
    secret_input = message.text
    data = await state.get_data()
    teacher = data['teacher']
    
    correct_secret = db.get_secret(teacher)
    
    if secret_input == correct_secret:
        # Ro'yxatdan o'tishni yakunlash
        group_info = f"{teacher} | {data['days']} | {data['time']}"
        
        db.add_user(
            message.from_user.id,
            data['full_name'],
            group_info,
            data['phone']
        )
        
        await message.answer("✅ Maxfiy so'z to'g'ri!\n✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", 
                           reply_markup=kb.user_menu())
        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri maxfiy so'z! Iltimos, qaytadan urinib ko'ring:")

@dp.callback_query(F.data == "cancel_reg")
async def cancel_registration(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Ro'yxatdan o'tish bekor qilindi.")

# ========== DARSLAR MENYUSI ==========
@dp.message(F.text == "📚 Darslar")
async def show_lessons(message: types.Message):
    await message.answer("Darslardan birini tanlang:", reply_markup=kb.lessons_pagination())

@dp.callback_query(F.data == "back_to_lessons")
async def back_to_lessons(call: types.CallbackQuery):
    """Darslar menyusiga qaytish"""
    await call.message.edit_text("Darslardan birini tanlang:", reply_markup=kb.lessons_pagination())

@dp.callback_query(F.data.startswith("page_"))
async def handle_pagination(call: types.CallbackQuery):
    page = int(call.data.split("_")[1])
    await call.message.edit_text(f"Sahifa {page}:", 
                               reply_markup=kb.lessons_pagination(page))

@dp.callback_query(F.data.startswith("lesson_"))
async def handle_lesson(call: types.CallbackQuery):
    lesson_num = int(call.data.split("_")[1])
    
    # O'qituvchini aniqlash
    user = db.get_user(call.from_user.id)
    teacher_name = None
    if user and len(user) > 2 and user[2]:
        # user[2] -> group_info. Format: "Teacher | Days | Time"
        parts = user[2].split("|")
        if len(parts) > 0:
            teacher_name = parts[0].strip()
            
    print(f"👨‍🎓 Student o'qituvchisi: {teacher_name}")

    await call.message.edit_text(f"Lesson {lesson_num}:", 
                               reply_markup=kb.lesson_menu(lesson_num))

# ========== CONTENT TURLARI ==========
@dp.callback_query(F.data.startswith("type_"))
async def handle_content_type(call: types.CallbackQuery):
    parts = call.data.split("_")
    lesson_num = int(parts[1])
    content_type = parts[2]
    
    # O'qituvchini aniqlash
    user = db.get_user(call.from_user.id)
    teacher_name = None
    if user and len(user) > 2 and user[2]:
        parts = user[2].split('|')
        if len(parts) > 0:
            teacher_name = parts[0].strip()
    
    # User None bo'lsa, xatolik berish
    if user is None:
        await call.answer("❌ Siz ro'yxatdan o'tmagansiz! Iltimos /start buyrug'i bilan ro'yxatdan o'ting.", show_alert=True)
        return
    
    # Teacher_name None bo'lsa, xatolik berish
    if teacher_name is None:
        await call.answer("❌ Sizning o'qituvchingiz ma'lum emas! Iltimos ro'yxatdan o'tishni qayta tekshiring.", show_alert=True)
        return
    

    # Kontentni olish
    content_parts = db.get_lesson_content(lesson_num, content_type, teacher_name)
    
    # Agar databaseda kontent bo'lmasa, kanaldan qidirish
    if not content_parts:
        print(f"🔍 Database da kontent yo'q, kanaldan qidirilmoqda...")
        try:
            # Kanaldan kontentni qidirish
            from aiogram import Bot
            bot_instance = Bot(token=BOT_TOKEN)
            
            # O'qituvchining kanalini topish
            teacher_channel_id = None
            if teacher_name == "Bunyod Shamsiddinov":
                teacher_channel_id = -1003887247702
            
            if teacher_channel_id:
                print(f"🔍 {teacher_name} kanalidan qidirilmoqda: {teacher_channel_id}")
                
                # Kanaldan so'nggi xabarlarni olish (bu ishlamaydi, lekin test qilamiz)
                # Aslida bu yerda kanaldan qidirish kerak, lekin aiogram cheklovlari bor
                print(f"⚠️ Kanaldan qidirish cheklangan, database ga asoslanamiz")
                
        except Exception as e:
            print(f"❌ Kanaldan qidirishda xatolik: {e}")
    
    if content_parts:
        try:
            reply_markup = kb.content_parts(lesson_num, content_type, content_parts)
            
            # Xabar matnini tayyorlash
            new_text = f"📚 {content_type.title()} - Lesson {lesson_num}:"
            
            # Xabar bir xil emasligini tekshirish
            try:
                await call.message.edit_text(
                    new_text, 
                    reply_markup=reply_markup
                )
                print(f"✅ Successfully sent content with {len(content_parts)} items")
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    print(f"⚠️ Message not modified, skipping edit")
                    await call.answer(f"📚 {content_type.title()} - Lesson {lesson_num} ({len(content_parts)} ta kontent)")
                else:
                    raise e
                    
        except Exception as e:
            print(f"❌ Error creating keyboard: {e}")
            await call.message.edit_text(
                f"❌ Xatolik yuz berdi: {e}", 
                reply_markup=kb.back_to_lessons()
            )
    else:
        print(f"❌ No content found for lesson {lesson_num}, type {content_type}")
        await call.answer(f"❌ {content_type} mavjud emas!", show_alert=True)

# ========== ADMIN COMMANDS ==========
@dp.message(F.text.in_({"/admin_content", "📋 Kontentlar"}))
async def admin_content_menu(message: types.Message):
    """Admin kontent menyu"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Siz admin emassiz!")
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Barcha kontentni ko'rish", callback_data="admin_view_all_content")
    keyboard.button(text="🔍 Dars bo'yicha ko'rish", callback_data="admin_view_lesson_content")
    keyboard.button(text="➕ Yangi kontent qo'shish", callback_data="admin_add_content")
    keyboard.button(text="🗑️ Kontent o'chirish", callback_data="admin_delete_content")
    keyboard.button(text="📊 Statistika", callback_data="admin_stats")
    keyboard.adjust(1)
    
    await message.answer(
        "👨‍💼 **ADMIN PANEL - KONTENT BOSHQARUV**\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=keyboard.as_markup()
    )

@dp.callback_query(F.data == "admin_view_all_content")
async def admin_view_all_content(call: types.CallbackQuery):
    """Barcha kontentni ko'rish"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    all_content = db.get_all_content()
    
    if not all_content:
        await call.message.edit_text("📋 **Kontent topilmadi!**")
        return
    
    text = "📋 **BARCHA KONTENT**\n\n"
    for content in all_content:
        hashtag = content[0]
        content_type = content[1]
        file_type = content[2]
        text += f"🏷️ `{hashtag}` - {content_type} ({file_type})\n"
    
    # Agar xabar juda uzun bo'lsa, bo'laklarga bo'lamiz
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await call.message.answer(part, parse_mode="HTML")
    else:
        await call.message.edit_text(text, parse_mode="HTML")
    
    await call.answer()

@dp.callback_query(F.data == "admin_view_lesson_content")
async def admin_view_lesson_content(call: types.CallbackQuery):
    """Dars bo'yicha kontentni ko'rish"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    
    # Darslar ro'yxatini yaratish
    for i in range(1, 49):  # 1-48 darslar
        keyboard.button(text=f"Dars {i}", callback_data=f"admin_lesson_{i}")
    
    keyboard.adjust(4)
    keyboard.button(text="⬅️ Orqaga", callback_data="admin_back_to_menu")
    
    await call.message.edit_text(
        "📚 **QAYSI DARSNI KO'RMOQCHISIZ?**\n\n"
        "Dars raqamini tanlang:",
        reply_markup=keyboard.as_markup()
    )

@dp.callback_query(F.data.startswith("admin_lesson_"))
async def admin_lesson_details(call: types.CallbackQuery):
    """Dars tafsilotlarini ko'rish"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    lesson_num = call.data.split("_")[2]
    
    # Shu darsdagi barcha kontentni olish
    lesson_content = []
    for content_type in ["listening", "reading", "grammar", "vocabulary"]:
        content = db.get_lesson_content(int(lesson_num), content_type)
        lesson_content.extend(content)
    
    if not lesson_content:
        await call.message.edit_text(f"📋 **Dars {lesson_num} uchun kontent topilmadi!**")
        return
    
    text = f"📚 **DARS {lesson_num} KONTENTI**\n\n"
    
    # Content type lar bo'yicha guruhlash
    content_groups = {}
    for item in lesson_content:
        hashtag = item[1]
        content_type = item[2]
        teacher_name = item[6]
        
        if content_type not in content_groups:
            content_groups[content_type] = []
        
        content_groups[content_type].append({
            'hashtag': hashtag,
            'teacher': teacher_name,
            'file_type': item[4]
        })
    
    for content_type, items in content_groups.items():
        text += f"🔹 **{content_type.upper()}:**\n"
        for item in items:
            text += f"  🏷️ `{item['hashtag']}` - {item['teacher']} ({item['file_type']})\n"
        text += "\n"
    
    # Agar xabar juda uzun bo'lsa
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        await call.message.answer(parts[0], parse_mode="HTML")
        if len(parts) > 1:
            await call.message.answer(parts[1], parse_mode="HTML")
    else:
        await call.message.edit_text(text, parse_mode="HTML")
    
    await call.answer()

@dp.callback_query(F.data == "admin_add_content")
async def admin_add_content(call: types.CallbackQuery):
    """Yangi kontent qo'shish"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    await call.message.edit_text(
        "➕ **YANGI KONTENT QO'SHISH**\n\n"
        "Format:\n"
        "`/add_content lesson1_listening_1 listening audio Bunyod_Shamsiddinov file_id_123`\n\n"
        "Yoki kanaldan forward qiling!"
    )

@dp.message(F.text.startswith("/add_content"))
async def process_add_content(message: types.Message):
    """Yangi kontent qo'shish"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 6:
            await message.answer("❌ Noto'g'ri format! Qayta urinib ko'ring.")
            return
        
        hashtag = parts[1]
        content_type = parts[2]
        file_type = parts[3]
        teacher_name = parts[4].replace("_", " ")
        file_id = parts[5] if len(parts) > 5 else None
        
        # Kontentni saqlash
        success = db.save_content(hashtag, content_type, file_id, file_type, 0, teacher_name)
        
        if success:
            await message.answer(
                f"✅ **KONTENT MUVOFFAQIYATLI QO'SHILDI!**\n\n"
                f"🏷️ Hashtag: `{hashtag}`\n"
                f"📝 Type: {content_type}\n"
                f"📁 File Type: {file_type}\n"
                f"👨‍🏫 Teacher: {teacher_name}"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi!")
            
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@dp.callback_query(F.data == "admin_delete_content")
async def admin_delete_content(call: types.CallbackQuery):
    """Kontent o'chirish"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    await call.message.edit_text(
        "🗑️ **KONTENT O'CHIRISH**\n\n"
        "O'chirish uchun hashtag yuboring:\n"
        "`/delete_content lesson1_listening_1`"
    )

@dp.message(F.text.startswith("/delete_content"))
async def process_delete_content(message: types.Message):
    """Kontentni o'chirish"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        hashtag = message.text.split()[1]
        
        # Kontentni olish va tekshirish
        content = db.get_content(hashtag)
        
        if not content:
            await message.answer(f"❌ `{hashtag}` topilmadi!")
            return
        
        # Kontentni o'chirish
        db.execute("DELETE FROM content WHERE hashtag = ?", (hashtag,))
        
        await message.answer(
            f"✅ **KONTENT O'CHIRILDI!**\n\n"
            f"🏷️ Hashtag: `{hashtag}`"
        )
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: types.CallbackQuery):
    """Statistika"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    # Statistikani olish
    total_content = len(db.get_all_content())
    active_users = db.get_active_users_count()
    
    text = f"📊 **STATISTIKA**\n\n"
    text += f"📚 Jami kontentlar: {total_content} ta\n"
    text += f"👥 Aktiv foydalanuvchilar: {active_users} ta\n"
    
    # Content type lar bo'yicha statistika
    content_types = {"listening": 0, "reading": 0, "grammar": 0, "vocabulary": 0}
    all_content = db.get_all_content()
    
    for content in all_content:
        content_type = content[1]
        if content_type in content_types:
            content_types[content_type] += 1
    
    text += "\n📈 **Content Type lar:**\n"
    for content_type, count in content_types.items():
        text += f"  🔹 {content_type}: {count} ta\n"
    
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "admin_back_to_menu")
async def admin_back_to_menu(call: types.CallbackQuery):
    """Admin menuga qaytish"""
    if call.from_user.id not in ADMINS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Barcha kontentni ko'rish", callback_data="admin_view_all_content")
    keyboard.button(text="🔍 Dars bo'yicha ko'rish", callback_data="admin_view_lesson_content")
    keyboard.button(text="➕ Yangi kontent qo'shish", callback_data="admin_add_content")
    keyboard.button(text="🗑️ Kontent o'chirish", callback_data="admin_delete_content")
    keyboard.button(text="📊 Statistika", callback_data="admin_stats")
    keyboard.adjust(1)
    
    await call.message.edit_text(
        "👨‍💼 **ADMIN PANEL - KONTENT BOSHQARUV**\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=keyboard.as_markup()
    )

# ========== KANAL POSTLARINI AVTOMATIK SAQLASH ==========
@dp.channel_post()
@dp.edited_channel_post()
async def handle_channel_post(message: types.Message):
    """Kanaldagi xabarlarni avtomatik ravishda saqlash"""
    import re
    
    channel_id = message.chat.id
    print(f"📡 Kanal post keldi: Chat ID={channel_id}, Type={message.content_type}")
    
    # O'qituvchini kanalga qarab aniqlash
    teacher_name = db.get_channel_teacher(channel_id)
    if not teacher_name:
        print(f"❌ Noma'lum kanal: {channel_id}. Kanallar: {db.get_all_channels()}")
        return
    
    print(f"✅ Ustoz: {teacher_name}")
    
    # Text yoki caption
    text = message.text or message.caption or ""
    if not text or "#" not in text:
        return
    
    print(f"📝 Text: {text[:100]}")
    hashtags = re.findall(r'#\w+', text)
    print(f"🏷️ Hashtag'lar: {hashtags}")
    
    for hashtag in hashtags:
        hashtag_lower = hashtag.lower()  # DOIM lowercase saqlash!
        
        if not hashtag_lower.startswith("#lesson"):
            continue
        
        # Hashtag dan ma'lumot olish: #lesson1_listening_1
        inner = hashtag_lower.replace("#", "")  # lesson1_listening_1
        parts = inner.split("_")
        
        if len(parts) < 3:
            print(f"⚠️ Noto'g'ri hashtag format: {hashtag_lower}")
            continue
        
        content_type = parts[1]  # listening, reading, grammar, vocabulary
        
        if content_type not in ('listening', 'reading', 'grammar', 'vocabulary'):
            print(f"⚠️ Noma'lum content type: {content_type}")
            continue
        
        # File ID olish
        file_id = None
        file_type = "text"
        
        if message.audio:
            file_id = message.audio.file_id
            file_type = "audio"
        elif message.voice:
            file_id = message.voice.file_id
            file_type = "voice"
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        else:
            # Text xabar — quiz link yoki matn
            file_id = text.strip()
            file_type = "text"
        
        if not file_id:
            print(f"❌ file_id topilmadi: {hashtag_lower}")
            continue
        
        # Database ga saqlash — db.save_content ichida ham .lower() bor
        try:
            success = db.save_content(
                hashtag=hashtag_lower,
                content_type=content_type,
                file_id=file_id,
                file_type=file_type,
                channel_msg_id=message.message_id,
                teacher_name=teacher_name
            )
            if success:
                print(f"✅ Saqlandi: {hashtag_lower} ({file_type}) — {teacher_name}")
            else:
                print(f"❌ Saqlanmadi: {hashtag_lower}")
        except Exception as e:
            print(f"❌ Saqlashda xatolik [{hashtag_lower}]: {e}")

@dp.channel_post(F.content_type.in_({'photo', 'audio', 'video', 'document'}))
async def handle_channel_media(message: types.Message):
    """Kanaldagi media fayllarni tekshirish"""
    # Agar text bo'lsa, yuqoridagi handler ishlaydi
    if message.text:
        return
    
    print(f"📡 Kanal media keldi (text yo'q): {message.content_type}")
    
    # Caption da hashtag borligini tekshirish
    if message.caption and "#" in message.caption:
        # Yuqoridagi logikani qayta ishlatamiz
        await handle_channel_post(message)

# ========== KONTENT FORWARD QILISH ==========
@dp.message(F.content_type.in_({'photo', 'audio', 'video', 'document'}))
async def handle_forward_content(message: types.Message):
    """Kanaldan forward qilingan kontentni qayta ishlash"""
    if message.from_user.id not in ADMINS:
        return
    
    # Agar forward qilingan xabar bo'lsa
    if message.forward_from_chat:
        # File ID ni olish
        file_id = None
        file_type = None
        
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.audio:
            file_id = message.audio.file_id
            file_type = "audio"
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        
        await message.answer(
            "📤 **FORWARD KONTENT**\n\n"
            "Bu kontentni qo'shish uchun format:\n"
            "`/add_content lesson1_listening_1 listening audio Bunyod_Shamsiddinov`\n\n"
            f"File ID: `{file_id}`\n"
            f"File Type: `{file_type}`\n\n"
            "Yoki quyidagi formatda bevosita yuboring:\n"
            "`/add_content lesson1_listening_1 listening audio Bunyod_Shamsiddinov " + file_id + "`"
        )
    else:
        # Agar to'g'ridan-to'g'ri yuborilgan fayl bo'lsa
        file_id = None
        file_type = None
        
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.audio:
            file_id = message.audio.file_id
            file_type = "audio"
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        
        if file_id:
            await message.answer(
                "📎 **FAYL QABUL QILINDI**\n\n"
                "Bu faylni qo'shish uchun format:\n"
                "`/add_content lesson1_listening_1 listening audio Bunyod_Shamsiddinov`\n\n"
                f"File ID: `{file_id}`\n"
                f"File Type: `{file_type}`\n\n"
                "Yoki quyidagi formatda bevosita yuboring:\n"
                "`/add_content lesson1_listening_1 listening audio Bunyod_Shamsiddinov " + file_id + "`"
            )

@dp.message(F.text.startswith("/add_content"))
async def process_add_content(message: types.Message):
    """Yangi kontent qo'shish"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 5:
            await message.answer("❌ Noto'g'ri format! Qayta urinib ko'ring.\n\nFormat: `/add_content lesson1_listening_1 listening audio Bunyod_Shamsiddinov file_id`")
            return
        
        hashtag = parts[1]
        content_type = parts[2]
        file_type = parts[3]
        teacher_name = parts[4].replace("_", " ")
        
        # File ID ni tekshirish
        file_id = parts[5] if len(parts) > 5 else None
        
        if not file_id:
            await message.answer("❌ File ID kiritilmadi! Faylni yuboring yoki to'g'ri formatda kiriting.")
            return
        
        # Kontentni saqlash
        success = db.save_content(hashtag, content_type, file_id, file_type, 0, teacher_name)
        
        if success:
            await message.answer(
                f"✅ **KONTENT MUVOFFAQIYATLI QO'SHILDI!**\n\n"
                f"🏷️ Hashtag: `{hashtag}`\n"
                f"📝 Type: {content_type}\n"
                f"📁 File Type: {file_type}\n"
                f"👨‍🏫 Teacher: {teacher_name}\n"
                f"🆔 File ID: `{file_id}`"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi!")
            
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

# ========== TEZ KONTENT QO'SHISH ==========
@dp.message(F.text.startswith("/quick_add"))
async def quick_add_content(message: types.Message):
    """Tez kontent qo'shish - faqat hashtag va content_type"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Siz admin emassiz!")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("❌ Noto'g'ri format! Format: `/quick_add lesson32_listening_1 listening`")
            return
        
        hashtag = parts[1]
        content_type = parts[2]
        
        # Hashtag dan dars raqamini olish
        import re
        match = re.search(r'lesson(\d+)', hashtag)
        if not match:
            await message.answer("❌ Hashtag noto'g'ri formatda! Masalan: lesson32_listening_1")
            return
        
        lesson_num = match.group(1)
        
        # Default qiymatlar
        file_id = f"lesson{lesson_num}_{content_type}_file"
        file_type = "audio" if content_type == "listening" else "text"
        teacher_name = "Bunyod Shamsiddinov"
        
        # Kontentni saqlash
        success = db.save_content(hashtag, content_type, file_id, file_type, 0, teacher_name)
        
        if success:
            await message.answer(
                f"✅ **KONTENT TEZ QO'SHILDI!**\n\n"
                f"🏷️ Hashtag: `{hashtag}`\n"
                f"📝 Type: {content_type}\n"
                f"📁 File Type: {file_type}\n"
                f"👨‍🏫 Teacher: {teacher_name}\n"
                f"🆔 File ID: `{file_id}`\n\n"
                f"⚠️ Eslatma: Bu test kontent. Haqiqiy faylni keyinroq qo'shing!"
            )
        else:
            await message.answer("❌ Xatolik yuz berdi!")
            
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
@dp.callback_query(F.data == "check_both_subscriptions")
async def check_subscriptions(call: types.CallbackQuery, state: FSMContext):
    """Obuna bo'ldim tugmasi - to'g'ridan-to'g'ri ro'yxatdan o'tish"""
    user = db.get_user(call.from_user.id)
    
    if user:
        # Agar foydalanuvchi ro'yxatdan o'tgan bo'lsa, asosiy menuga o'tkazamiz
        await call.answer()
        await call.message.answer(
            "✅ <b>Rahmat! Obuna bo'lganingiz uchun tashakkur!</b>\n\n"
            "🎉 <i>Siz darslardan foydalanishingiz mumkin.</i>\n\n"
            "📚 <b>Bosh menyu:</b>",
            reply_markup=kb.user_menu(),
            parse_mode="HTML"
        )
    else:
        # Agar ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tishni boshlaymiz
        await call.answer()
        await call.message.answer(
            "✅ <b>Rahmat! Obuna bo'lganingiz uchun tashakkur!</b>\n\n"
            "📝 <b>Endi ro'yxatdan o'ting:</b>\n\n"
            "🎓 Ism va familiyangizni kiriting:",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(Registration.full_name)

# ========== ORQAGA QAYTISH ==========
@dp.callback_query(F.data == "back_to_lessons")
async def back_to_lessons(call: types.CallbackQuery):
    """Orqaga darslar menugasiga qaytish"""
    user = db.get_user(call.from_user.id)
    if not user:
        await call.message.edit_text(
            "❌ Siz ro'yxatdan o'tmagansiz!\n\n"
            "📝 Iltimos, /start buyrug'i bilan qayta ro'yxatdan o'ting.",
            reply_markup=kb.start_keyboard()
        )
        return
    
    # Foydalanuvchi darslarini olish
    user_lessons = db.get_user_lessons(call.from_user.id)
    if not user_lessons:
        await call.message.edit_text(
            "❌ Sizda darslar mavjud emas!\n\n"
            "📝 Iltimos, avval darsni tanlang.",
            reply_markup=kb.user_menu()
        )
        return
    
    # Darslar ro'yxatini ko'rsatish
    lessons_text = "📚 <b>Darslar ro'yxati:</b>\n\n"
    for lesson in user_lessons:
        lesson_num = lesson[0]
        lesson_name = lesson[1]
        lessons_text += f"🔹 <b>Dars {lesson_num}:</b> {lesson_name}\n"
    
    await call.message.edit_text(
        lessons_text,
        reply_markup=kb.lesson_menu(user_lessons),
        parse_mode="HTML"
    )

# ========== KONTENTNI YUBORISH ==========
@dp.callback_query(F.data.startswith("content_"))
async def send_content(call: types.CallbackQuery):
    hashtag = call.data.replace("content_", "")
    print(f"📤 Kontent so'raldi: {hashtag}")
    
    content = db.get_content(hashtag)
    print(f"🔍 Debug: content = {content}")
    print(f"🔍 Debug: content type = {type(content)}")
    
    if content:
        print(f"🔍 Debug: content length = {len(content)}")
        print(f"🔍 Debug: content[0] = {content[0]}")  # id
        print(f"🔍 Debug: content[1] = {content[1]}")  # hashtag
        print(f"🔍 Debug: content[2] = {content[2]}")  # content_type
        print(f"🔍 Debug: content[3] = {content[3]}")  # file_id
        print(f"🔍 Debug: content[4] = {content[4]}")  # file_type
        
        file_id = content[3]  # file_id (index 3)
        file_type = content[4]  # file_type (index 4)
        
        print(f"🔍 Debug: file_id = {file_id}")
        print(f"🔍 Debug: file_type = {file_type}")
        
        try:
            if file_type == "text":
                await call.message.answer(file_id)
            elif file_type == "photo":
                await bot.send_photo(call.from_user.id, file_id)
            elif file_type == "audio":
                await bot.send_audio(call.from_user.id, file_id)
            elif file_type == "video":
                await bot.send_video(call.from_user.id, file_id)
            elif file_type == "document":
                await bot.send_document(call.from_user.id, file_id)
            elif file_type == "voice":
                await bot.send_voice(call.from_user.id, file_id)
            
            await call.answer("✅ Yuborildi!")
            
        except Exception as e:
            print(f"❌ Kontent yuborishda xatolik: {e}")
            await call.answer(f"❌ Xatolik: {str(e)[:50]}", show_alert=True)
    else:
        await call.answer("❌ Kontent topilmadi!", show_alert=True)

# ========== ADMIN PANEL ==========
# Admin panel start_handler da boshqariladi

@dp.message(F.text == "👥 Barcha foydalanuvchilar", F.from_user.id.in_(ADMINS))
async def all_users_menu(message: types.Message):
    """Barcha foydalanuvchilarni xabar sifatida yuborish"""
    print("🔍 '👥 Barcha foydalanuvchilar' tugmasi bosildi")
    
    try:
        # Database dan ma'lumot olish
        users = db.get_all_users_for_excel()
        
        print(f"📊 {len(users)} ta foydalanuvchi topildi")
        
        if not users:
            await message.answer("❌ Foydalanuvchilar topilmadi!", reply_markup=kb.admin_menu())
            return
        
        # Foydalanuvchilar ro'yxatini yasash
        users_text = f"📊 <b>Barcha foydalanuvchilar ro'yxati</b>\n\n"
        users_text += f"👥 Jami foydalanuvchilar: {len(users)} ta\n"
        users_text += f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        users_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, user in enumerate(users, 1):
            users_text += f"👤 <b>{i}. {user[1]}</b>\n"
            users_text += f"🆔 ID: <code>{user[0]}</code>\n"
            users_text += f"📞 Tel: {user[2]}\n"
            users_text += f"👥 Guruh: {user[3]}\n"
            users_text += f"📷 Instagram: {'✅' if user[4] else '❌'} {user[5] if user[5] else ''}\n"
            users_text += f"🟢 Status: {user[6]}\n"
            users_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Excel export taklifi
        users_text += "📥 <b>Excel faylni yuborish uchun:</b>\n"
        users_text += "💬 <code>/excel_users</code> deb yozing\n\n"
        
        # Xabar bo'laklarga bo'lib yuborish (agar juda uzun bo'lsa)
        if len(users_text) > 4000:
            # Birinchi qism
            first_part = users_text[:3500] + "\n\n<i>...Davomi keyingi xabarda...</i>"
            await message.answer(first_part, parse_mode="HTML")
            
            # Qolgan qism
            remaining_part = "📊 <b>Foydalanuvchilar ro'yxati (davomi)</b>\n\n" + users_text[3500:]
            await message.answer(remaining_part, parse_mode="HTML")
        else:
            await message.answer(users_text, parse_mode="HTML")
        
        print(f"✅ {len(users)} ta foydalanuvchi ro'yxati yuborildi!")
        
    except Exception as e:
        print(f"❌ XATOLIK: {e}")
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)[:50]}", reply_markup=kb.admin_menu())

@dp.message(F.text == "🔑 Maxfiy so'zlar", F.from_user.id.in_(ADMINS))
async def manage_secrets_text(message: types.Message):
    secrets = db.get_all_secrets()
    await message.answer(
        "🔑 <b>Maxfiy so'zlar boshqaruvi</b>\n\n"
        f"Joriy maxfiy so'zlar:\n{secrets}",
        reply_markup=kb.secrets_management_menu(),
        parse_mode="HTML"
    )

# ========== BROADCAST ==========
@dp.message(F.text == "📢 Barchaga xabar yuborish", F.from_user.id.in_(ADMINS))
async def broadcast_start(message: types.Message, state: FSMContext):
    """Barchaga xabar yuborishni boshlash"""
    await message.answer(
        "📢 <b>Barchaga Xabar Yuborish</b>\n\n"
        "📝 <b>Reklama xabarini yuboring:</b>\n\n"
        "💡 <i>Ikkita usul bor:</i>\n"
        "1️⃣ <b>Rasm + Caption</b> - rasm yuboring, caption ga matn yozing\n"
        "2️⃣ <b>Faqat Matn</b> - faqat matn yuboring\n\n"
        "🎨 <i>HTML formatdan foydalanishingiz mumkin:</i>\n"
        "• <b>Qalin matn</b>\n"
        "• <i>Kursiv matn</i>\n"
        "• <code>Kod</code>\n"
        "• <a href='link'>Havola</a>\n\n"
        "📸 <i>Tavsiya: Reklama uchun rasm + caption ko'proq samara beradi</i>",
        reply_markup=kb.cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminState.waiting_broadcast_message)

@dp.message(AdminState.waiting_broadcast_message)
async def broadcast_message_input(message: types.Message, state: FSMContext):
    """Xabar matnini qabul qilish"""
    text = message.text or message.caption
    
    if not text:
        await message.answer("❌ Xatolik! Iltimos, matn yoki caption bilan xabar yuboring.")
        return
    
    await state.update_data(broadcast_text=text)
    
    # Agar rasm bilan birga yuborilgan bo'lsa
    if message.photo:
        await state.update_data(broadcast_photo=message.photo[-1].file_id)
        
        # Xabarni ko'rsatish
        try:
            # Adminga namuna yuborish
            await bot.send_photo(
                chat_id=message.from_user.id,
                photo=message.photo[-1].file_id,
                caption=text,
                parse_mode="HTML"
            )
            
            await message.answer(
                "✅ <b>Xabar qabul qilindi!</b>\n\n"
                "📸 <b>Yuqoragi rasmli xabarni barchaga yuboraymi?</b>\n\n"
                "� <i>Barcha foydalanuvchilar: {len(db.get_all_users())} ta</i>\n\n"
                "➡️ <i>Yuborish uchun 'Ha' deb yozing</i>\n"
                "➡️ <i>Bekor qilish uchun /cancel_admin</i>",
                reply_markup=kb.cancel_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")
        
        await state.set_state(AdminState.waiting_broadcast_confirmation)
    else:
        # Faqat matn
        await message.answer(
            "� <b>Faqat matnli xabar qabul qilindi!</b>\n\n"
            f"� <b>Xabar matni:</b>\n\n{text}\n\n"
            "📸 <i>Rasm qo'shish uchun rasm yuboring</i>\n"
            "➡️ <i>Faqat shu matnni yuborish uchun 'Ha' deb yozing</i>\n"
            "➡️ <i>Bekor qilish uchun /cancel_admin</i>",
            reply_markup=kb.cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AdminState.waiting_broadcast_confirmation)

@dp.message(AdminState.waiting_broadcast_confirmation, F.photo)
async def broadcast_with_photo(message: types.Message, state: FSMContext):
    """Rasmli xabar yuborish"""
    if message.text and message.text.lower() == 'ha':
        data = await state.get_data()
        text = data.get('broadcast_text')
        
        if not text:
            await message.answer("❌ Xatolik! Qaytadan urinib ko'ring.")
            await state.clear()
            return
        
        # Barcha foydalanuvchilarni olish
        users = db.get_all_users()
        
        await message.answer("📤 <b>Xabar yuborilmoqda...</b>", parse_mode="HTML")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                await bot.send_photo(
                    chat_id=user[0],
                    photo=message.photo[-1].file_id,
                    caption=text,
                    parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                print(f"❌ Xabar yuborilmadi {user[0]} ga: {e}")
                error_count += 1
        
        await message.answer(
            f"✅ <b>Rasmli xabar yuborildi!</b>\n\n"
            f"📊 <b>Statistika:</b>\n"
            f"✅ Muvaffaqiyatli: {success_count} ta\n"
            f"❌ Xatolik: {error_count} ta\n"
            f"📊 Jami: {len(users)} ta foydalanuvchi",
            reply_markup=kb.admin_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await message.answer("❌ Iltimos, 'Ha' deb yozing yoki /cancel_admin")

@dp.message(AdminState.waiting_broadcast_confirmation)
async def broadcast_text_only(message: types.Message, state: FSMContext):
    """Textli xabarni yuborishni tasdiqlash"""
    if message.text and message.text.lower() == 'ha':
        data = await state.get_data()
        text = data.get('broadcast_text')
        photo_id = data.get('broadcast_photo')
        
        if not text:
            await message.answer("❌ Xatolik! Qaytadan urinib ko'ring.")
            await state.clear()
            return
        
        # Barcha foydalanuvchilarni olish
        users = db.get_all_users()
        
        await message.answer("📤 <b>Xabar yuborilmoqda...</b>", parse_mode="HTML")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                if photo_id:
                    # Rasmli xabar
                    await bot.send_photo(
                        chat_id=user[0],
                        photo=photo_id,
                        caption=text,
                        parse_mode="HTML"
                    )
                else:
                    # Faqat matn
                    await message.answer(
                        text=text,
                        chat_id=user[0],
                        parse_mode="HTML"
                    )
                success_count += 1
            except Exception as e:
                print(f"❌ Xabar yuborilmadi {user[0]} ga: {e}")
                error_count += 1
        
        message_type = "Rasmli" if photo_id else "Matnli"
        await message.answer(
            f"✅ <b>{message_type} xabar yuborildi!</b>\n\n"
            f"📊 <b>Statistika:</b>\n"
            f"✅ Muvaffaqiyatli: {success_count} ta\n"
            f"❌ Xatolik: {error_count} ta\n"
            f"📊 Jami: {len(users)} ta foydalanuvchi",
            reply_markup=kb.admin_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await message.answer("❌ Iltimos, 'Ha' deb yozing yoki /cancel_admin")

@dp.message(F.text == "🏠 Asosiy menyu", F.from_user.id.in_(ADMINS))
async def back_to_main_from_admin(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=kb.admin_menu())

@dp.callback_query(F.data == "excel_all_users")
async def excel_all_users(call: types.CallbackQuery):
    """Barcha foydalanuvchilarni Excel faylga chiqarish"""
    print("🔍 '📊 Barcha foydalanuvchilar' callback chaqirildi")
    
    try:
        # Database dan ma'lumot olish
        import sqlite3
        conn = sqlite3.connect('edu_star.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT telegram_id, full_name, phone, group_info, instagram_followed, instagram_username, 
                   CASE WHEN is_active = 1 THEN '✅ Faol' ELSE '❌ Nofaol' END as status
            FROM users 
            ORDER BY full_name
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        print(f"📊 {len(users)} ta foydalanuvchi topildi")
        
        if not users:
            await call.answer("❌ Foydalanuvchilar topilmadi!", show_alert=True)
            return
        
        # DataFrame yaratish
        df = pd.DataFrame(users, columns=[
            'Telegram ID', 'Ism Familiya', 'Telefon', 'Guruh', 
            'Instagram Obunasi', 'Instagram Username', 'Status'
        ])
        
        # Fayl nomi
        filename = f"barcha_foydalanuvchilar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        import os
        filepath = os.path.join(os.getcwd(), filename)
        
        # Excel faylni saqlash
        df.to_excel(filepath, index=False)
        print(f"✅ Excel fayl yaratildi: {filename}")
        
        # Faylni yuborish
        await call.message.answer_document(
            FSInputFile(filepath),
            caption=f"📊 Barcha foydalanuvchilar ({len(users)} ta)\n\n"
                   f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Faylni o'chirish
        import os
        os.remove(filepath)
        
        await call.answer(f"✅ {len(users)} ta foydalanuvchi yuborildi!")
        
    except Exception as e:
        print(f"❌ XATOLIK: {e}")
        await call.answer(f"❌ Xatolik: {str(e)[:50]}", show_alert=True)

@dp.callback_query(F.data == "excel_by_groups")
async def excel_by_groups(call: types.CallbackQuery):
    """Guruhlar bo'yicha foydalanuvchilarni Excel faylga chiqarish"""
    print("🔍 '👥 Guruhlar bo'yicha' callback chaqirildi")
    
    try:
        # Database dan ma'lumot olish
        import sqlite3
        conn = sqlite3.connect('edu_star.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT telegram_id, full_name, phone, group_info, instagram_followed, instagram_username, 
                   CASE WHEN is_active = 1 THEN '✅ Faol' ELSE '❌ Nofaol' END as status
            FROM users 
            ORDER BY group_info, full_name
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        print(f"� {len(users)} ta foydalanuvchi topildi")
        
        if not users:
            await call.answer("❌ Foydalanuvchilar topilmadi!", show_alert=True)
            return
        
        # Guruhlarni guruhlash
        groups_data = {}
        for user in users:
            group = user[3]  # group_info column
            if group not in groups_data:
                groups_data[group] = []
            groups_data[group].append(user)
        
        # Excel fayl yaratish
        filename = f"guruhlar_bo_yicha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        import os
        filepath = os.path.join(os.getcwd(), filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for group_name, group_users in groups_data.items():
                df = pd.DataFrame(group_users, columns=[
                    'Telegram ID', 'Ism Familiya', 'Telefon', 'Guruh', 
                    'Instagram Obunasi', 'Instagram Username', 'Status'
                ])
                df.to_excel(writer, sheet_name=str(group_name)[:31], index=False)
        
        print(f"✅ Excel fayl yaratildi: {filename}")
        
        # Faylni yuborish
        await call.message.answer_document(
            FSInputFile(filepath),
            caption=f"👥 Guruhlar bo'yicha foydalanuvchilar ({len(groups_data)} ta guruh, {len(users)} ta foydalanuvchi)\n\n"
                   f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Faylni o'chirish
        import os
        os.remove(filepath)
        
        await call.answer(f"✅ {len(groups_data)} ta guruh bo'yicha {len(users)} ta foydalanuvchi yuborildi!")
        
    except Exception as e:
        print(f"❌ XATOLIK: {e}")
        await call.answer(f"❌ Xatolik: {str(e)[:50]}", show_alert=True)

@dp.callback_query(F.data == "admin_back")
async def admin_back(call: types.CallbackQuery):
    print(f"🔍 admin_back callback chaqirildi: {call.data}")
    await call.message.edit_text("Admin panel:", reply_markup=kb.admin_menu())

# ========== MAIN FUNCTION ==========
async def main():
    print("============================================================")
    print("🤖 EDU STAR BOT ISHGA TUSHDI")
    print("============================================================")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Kanal ID: {CHANNEL_ID}")
    print(f"🔗 Kanal URL: {CHANNEL_URL}")
    print(f"📚 Darslar: 48 ta")
    print("============================================================")
    
    # JSON va database ni sinxronizatsiya qilish
    print("🔄 Maxfiy so'zlar sinxronizatsiyasi...")
    sync_secrets_to_db()
    print("✅ Maxfiy so'zlar sinxronizatsiya yakunlandi!")
    
    # Botni ishga tushirish
    await dp.start_polling(bot)
    print("🎯 Bot kanalni kuzatadi")
    print("🎯 Barcha ma'lumotlar kanaldan olinadi")
    print("🎯 Hashtag'lar bilan ishlaydi")
    print("🎯 Debug uchun: /debug (admin uchun)")
    print("============================================================")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot to'xtatildi.")
