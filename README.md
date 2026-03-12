# 🤖 EDU STAR BOT - TO'LIQ DOKUMENTATSIYA

## 📋 BO'T HAQIDA
Edu Star Bot - Telegram uchun ta'lim boti. Foydalanuvchilarni ro'yxatdan o'tkazadi, kanalga obuna bo'lishini tekshiradi, quiz o'tkazadi va Instagram obunasini boshqaradi.

## 🔧 ASOSIY FUNKSIYALAR

### 👤 Foydalanuvchi uchun:
- **Ro'yxatdan o'tish** - Ism, telefon, guruh tanlash
- **Kanal obunasi tekshiruvi** - Majburiy obuna
- **Instagram obunasi** - Ixtiyoriy obuna tekshiruvi
- **Quiz o'tkazish** - Savollar va javoblar
- **Darslarga kirish** - Ta'lim materiallari

### 👑 Admin uchun:
- **Admin paneli** - To'liq boshqaruv
- **Barchaga xabar yuborish** - Textli yoki rasmli
- **Foydalanuvchilar ro'yxati** - Excel export
- **Guruhlar bo'yicha statistika** - Excel export
- **Baza boshqaruvi** - O'qituvchi kanallari
- **Maxfiy so'zlar** - Ro'yxatdan o'tish so'zlari
- **Blok/Blokdan chiqarish** - Foydalanuvchilar boshqaruvi

## 📁 FAYL STRUKTURASI

```
Edu_Star_Bot/
├── main.py                 # Asosiy bot fayli
├── database.py             # Database klassi
├── keyboards.py            # Keyboardlar
├── states.py               # FSM holatlari
├── middleware.py           # Middleware
├── config.py               # Konfiguratsiya
├── .env                    # Maxfiy ma'lumotlar
├── database.db             # SQLite database
├── README.md              # Shu fayl
└── requirements.txt        # Kutubxonalar
```

## 🗄️ DATABASE TABELLARI

### `users` - Foydalanuvchilar
```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    full_name TEXT,
    phone TEXT,
    group_info TEXT,
    instagram_followed BOOLEAN DEFAULT 0,
    instagram_username TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `quiz_results` - Quiz natijalari
```sql
CREATE TABLE quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    question_id INTEGER,
    answer TEXT,
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `teacher_secrets` - Maxfiy so'zlar
```sql
CREATE TABLE teacher_secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT,
    secret_word TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `teacher_channels` - O'qituvchi kanallari
```sql
CREATE TABLE teacher_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT,
    teacher_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `blocked_users` - Bloklangan foydalanuvchilar
```sql
CREATE TABLE blocked_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    reason TEXT,
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `instagram_users` - Instagram foydalanuvchilari
```sql
CREATE TABLE instagram_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    instagram_username TEXT,
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 FSM HOLATLARI

### `RegistrationState` - Ro'yxatdan o'tish
- `waiting_full_name` - Ismni kiritish
- `waiting_phone` - Telefon raqamini kiritish
- `waiting_group` - Guruhni tanlash
- `waiting_instagram` - Instagram obunasi

### `QuizState` - Quiz
- `taking_quiz` - Quiz o'tkazish

### `AdminState` - Admin holatlari
- `waiting_broadcast_message` - Xabar matnini kiritish
- `waiting_broadcast_confirmation` - Xabar tasdiqlashi
- `waiting_block_reason` - Blok sababi
- `waiting_unblock_id` - Blokdan chiqarish ID
- `waiting_new_secret` - Yangi maxfiy so'z
- `waiting_channel_link` - Kanal linki

## 🔝 CALLBACK DATA

### Admin panel callback lar:
- `excel_all_users` - Barcha foydalanuvchilarni Excelga
- `excel_by_groups` - Guruhlar bo'yicha Excel
- `admin_back` - Admin paneliga qaytish
- `add_channel_menu` - Yangi kanal qo'shish
- `add_channel_{teacher}` - O'qituvchiga kanal qo'shish
- `delete_channel_{channel_id}` - Kanalni o'chirish
- `cancel_channel_add` - Kanal qo'shishni bekor qilish
- `database_back` - Baza menyusiga qaytish

### Foydalanuvchi callback lar:
- `confirm_update` - Ma'lumotlarni tozalashni tasdiqlash
- `cancel_update` - Bekor qilish

## 📱 KEYBOARDLAR

### ReplyKeyboardMarkup:
- `main_menu()` - Asosiy menyu
- `admin_menu()` - Admin menyu
- `contact_keyboard()` - Kontakt yuborish
- `cancel_keyboard()` - Bekor qilish

### InlineKeyboardMarkup:
- `users_management_menu()` - Foydalanuvchilar boshqaruvi
- `secrets_management_menu()` - Maxfiy so'zlar boshqaruvi

## 🚀 ISHLASH PRINSIPI

### 1️⃣ Ro'yxatdan o'tish:
1. Foydalanuvchi `/start` buyrug'ini yuboradi
2. Bot kanalga obunani tekshiradi
3. Ism, telefon, guruh so'raydi
4. Instagram obunasini tekshiradi (agar kerak bo'lsa)
5. Ma'lumotlarni database ga saqlaydi

### 2️⃣ Quiz:
1. Foydalanuvchi quizni boshlaydi
2. Savollar ketma-ket keladi
3. Javoblarni tekshiradi
4. Natijalarni saqlaydi

### 3️⃣ Admin funktsiyalari:
1. Admin paneliga kirish
2. Kerakli funktsiyani tanlash
3. Amallarni bajarish
4. Natijalarni olish

## 🔧 KONFIGURATSIYA

### `.env` fayli:
```env
# Bot token
BOT_TOKEN=your_bot_token_here

# Admin ID
ADMIN_ID=5964436818

# Kanal ma'lumotlari
CHANNEL_ID=-1003534326655
CHANNEL_URL=https://t.me/+ycUUFcckXqVhMzc6

# Instagram sozlamalari
INSTAGRAM_URL=https://www.instagram.com/your_instagram_profile
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_REQUIRED=false
```

### `config.py`:
```python
# O'qituvchilar ro'yxati
TEACHERS = ["O'qituvchi 1", "O'qituvchi 2", "O'qituvchi 3", "O'qituvchi 4"]

# Quiz savollari
QUESTIONS = [
    {"id": 1, "question": "Savol matni", "answer": "To'g'ri javob"},
    # ...
]
```

## 📊 STATISTIKA

### Bot ma'lumotlari:
- **Admin ID**: 5964436818
- **Kanal ID**: -1003534326655
- **Kanal URL**: https://t.me/+ycUUFcckXqVhMzc6
- **Darslar soni**: 48 ta

### Database ma'lumotlari:
- **Barcha foydalanuvchilar**: `SELECT COUNT(*) FROM users`
- **Faol foydalanuvchilar**: `SELECT COUNT(*) FROM users WHERE is_active = 1`
- **Bloklanganlar**: `SELECT COUNT(*) FROM blocked_users`

## 🛠️ QAYTA YUKLASH

### 1️⃣ Kutubxonalarni o'rnatish:
```bash
pip install aiogram pandas openpyxl python-dotenv
```

### 2️⃣ Konfiguratsiya:
1. `.env` faylini yaratish
2. Token va ID larni kiritish
3. Database ni yaratish

### 3️⃣ Botni ishga tushirish:
```bash
python main.py
```

## 🐛 XATOLIKLAR VA YO'LLAR

### Umumiy xatoliklar:
- **TelegramConflictError** - Token noto'g'ri
- **Database xatoliklari** - SQL so'rovlar
- **FSMContext xatoliklari** - State noto'g'ri

### Yechimlar:
- Tokenni tekshirish
- Database ni tekshirish
- State larni to'g'ri boshqarish

## 📞 YORDAM

### Debug uchun:
- `/debug` buyrug'i (admin uchun)
- Terminal loglari
- Database tekshiruvi

### Muh funktsiyalar:
- **Barchaga xabar yuborish** - Textli va rasmli
- **Excel export** - Barcha foydalanuvchilar va guruhlar bo'yicha
- **Baza boshqaruvi** - Kanallar va o'qituvchilar
- **Maxfiy so'zlar** - Ro'yxatdan o'tish boshqaruvi

---

**🤖 EDU STAR BOT** - To'liq ta'lim tizimi uchun bot
