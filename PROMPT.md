# EDU STAR BOT - TO'LIQ TAVSIF

## 🎯 **BOTNING ASOSIY MAQSADI**

Edu Star Bot - bu ingliz tili o'qituvchilari va o'quvchilari uchun mo'ljallangan Telegram boti. Bot o'quvchilarga dars materiallarini, testlarni va quizlarni o'qituvchilariga qarab tarqatadi.

## 🏗️ **ARHITEKTURA VA TEXNOLOGIYALAR**

### **Backend Texnologiyalari:**
- **Python 3.11+** - Asosiy dasturlash tili
- **aiogram 3.x** - Telegram bot framework
- **SQLite** - Ma'lumotlar bazasi
- **AsyncIO** - Asinxron ishlash

### **Asosiy Komponentlar:**
- **main.py** - Botning asosiy logikasi va handlerlar
- **database.py** - Ma'lumotlar bazasi bilan ishlash
- **keyboards.py** - Inline tugmalar va interfeys
- **config.py** - Konfiguratsiya va sozlamalar
- **states.py** - FSM holatlari
- **middleware.py** - Middlewarelar

## 📊 **MA'LUMOTLAR BAZASI STRUKTURASI**

### **Jadvallar:**

#### **1. USERS TABLE**
```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    full_name TEXT,
    group_info TEXT,           -- "O'qituvchi | Kunlar | Vaqt"
    phone TEXT,
    instagram_followed INTEGER DEFAULT 0,
    instagram_username TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### **2. CONTENT TABLE**
```sql
CREATE TABLE content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hashtag TEXT,              -- #lesson1_listening_1
    content_type TEXT,         -- listening, reading, grammar, vocabulary, quiz
    file_id TEXT,              -- Telegram file_id yoki text
    file_type TEXT,            -- text, photo, audio, video, document
    channel_msg_id INTEGER,
    teacher_name TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### **3. QUIZZES TABLE**
```sql
CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hashtag TEXT,
    lesson_num INTEGER,
    questions TEXT,            -- JSON formatda
    total_questions INTEGER,
    teacher_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### **4. TEACHER_SECRETS TABLE**
```sql
CREATE TABLE teacher_secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT UNIQUE,
    secret_word TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### **5. TEACHER_CHANNELS TABLE**
```sql
CREATE TABLE teacher_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER,
    teacher_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🔧 **BOTNING ASOSIY FUNKSIYALARI**

### **1. RO'YXATDAN O'TISH (Registration)**
- **/start** buyrug'i bilan boshlanadi
- Foydalanuvchi to'liq ismini, telefon raqamini kiritadi
- Instagram profiliga obuna bo'lishi (ixtiyoriy)
- O'qituvchini tanlaydi (kunlar va vaqtni ko'rsatadi)
- Maxfiy so'z orqali tasdiqlanadi

### **2. DARSLAR MENYUSI**
- 48 ta dars (1-48)
- Har bir dars uchun content turlari:
  - 🎧 **Listening** - Audio materiallar
  - 📖 **Reading** - Matnlar
  - 📚 **Grammar** - Grammatika qoidalar
  - 📝 **Vocabulary** - So'zlar
  - 🧪 **Quiz** - Testlar (faqat Bunyod Shamsiddinov uchun)

### **3. CONTENT FILTRLASH**
- **Hashtag asosida:** `#lesson1_listening_1`
- **O'qituvchiga qarab:** Har bir o'qituvchining o'z kontenti
- **Dars raqamiga qarab:** Faqat tanlangan dars kontenti
- **Content type ga qarab:** listening, reading, grammar, vocabulary

### **4. KONTENTNI YETKAZISH**
- **Text:** To'g'ridan-to'g'ri xabar sifatida
- **Audio:** Telegram audio fayli sifatida
- **Photo:** Telegram rasm sifatida
- **Video:** Telegram video sifatida
- **Quiz:** Tashqi havola orqali

## 👥 **FOYDALANUVCHI ROLLARI**

### **1. O'QUVCHILAR (Students)**
- Ro'yxatdan o'tishadi
- O'z o'qituvchisiga tegishli kontentni ko'radi
- Quizlarni yechishi mumkin (faqat o'z o'qituvchisi uchun)

### **2. O'QITUVCHILAR (Teachers)**
- Maxfiy so'zga ega
- O'z kanallariga kontent yuklaydi
- O'z o'quvchilariga kontent beradi

### **3. ADMINLAR (Admins)**
- Botni boshqaradi
- Foydalanuvchilarni bloklaydi
- Statistikani ko'radi

## 🔍 **KONTENT QIDIRISH ALGORITMI**

### **SQL LIKE Query:**
```sql
SELECT * FROM content 
WHERE hashtag LIKE '#lesson1_listening_%' 
AND content_type = 'listening' 
AND teacher_name = 'Bunyod Shamsiddinov'
ORDER BY saved_at DESC
```

### **Hashtag Formatlari:**
- `#lesson1_listening_1` - 1-dars listening 1-qism
- `#lesson1_reading_1` - 1-dars reading 1-qism
- `#lesson1_quiz` - 1-dars quiz
- `#lesson2_listening_1` - 2-dars listening 1-qism

## 🚀 **BOTNING ISHLASH PRINSIPI**

### **1. START FLOW:**
1. Foydalanuvchi `/start` buyrug'ini yuboradi
2. Bot to'liq ismni so'raydi
3. Bot telefon raqamini so'raydi
4. Bot Instagramga obuna bo'lishni taklif qiladi
5. Bot o'qituvchini tanlashni taklif qiladi
6. Bot maxfiy so'zni so'raydi
7. Bot ro'yxatdan o'tishni tugatadi

### **2. CONTENT FLOW:**
1. Foydalanuvchi "Darslar" tugmasini bosadi
2. Bot darslar ro'yxatini ko'rsatadi (1-48)
3. Foydalanuvchi dars raqamini tanlaydi
4. Bot content turlarini ko'rsatadi
5. Foydalanuvchi content turini tanlaydi
6. Bot kontentlarni ko'rsatadi
7. Foydalanuvchi kontentni tanlaydi
8. Bot kontentni yuboradi

### **3. QUIZ FLOW:**
1. Foydalanuvchi Quiz tugmasini bosadi
2. Bot o'qituvchini tekshiradi (faqat Bunyod Shamsiddinov)
3. Agar to'g'ri bo'lsa, quiz havolasini ko'rsatadi
4. Aks holda xatolik xabari beradi

## 📋 **KONFIGURATSIYA**

### **Environment Variables:**
- `BOT_TOKEN` - Telegram bot token
- `ADMIN_ID` - Admin telegram ID
- `ADMINS` - Adminlar ro'yxati
- `CHANNEL_ID` - Asosiy kanal ID
- `CHANNEL_URL` - Kanal URL

### **O'qituvchilar:**
- Bunyod Shamsiddinov
- Shohrux Abdurazzoqov
- Timur Normurodov
- Sirojiddin Norboyev

### **Maxfiy So'zlar:**
- Bunyod Shamsiddinov: "b2024"
- Shohrux Abdurazzoqov: "s2024"
- Timur Normurodov: "t2024"
- Sirojiddin Norboyev: "s2024"

## 🔧 **ASOSIY HUSUSIYATLAR**

### **Xavfsizlik:**
- Maxfiy so'zlar bilan himoya
- Adminlar uchun ro'yxatdan o'tish
- Foydalanuvchilarni bloklash imkoniyati

### **Shaxsiylashtirish:**
- Har bir o'quvchi o'z o'qituvchisining kontentini oladi
- Hashtag asosida aniq filtrlash
- Kunlar va vaqtlarga qarab guruhlash

### **Performance:**
- Async/await pattern
- SQLite optimallashtirilgan querylar
- Minimal debug loglar
- Tezkor javob berish

## 📊 **STATISTIKA VA MONITORING**

### **Kuzatuv:**
- Foydalanuvchilar soni
- Aktiv o'quvchilar
- Kontent yuklanmalari
- Quiz natijalari

### **Admin funktsiyalari:**
- Foydalanuvchilarni bloklash
- Statistikani ko'rish
- Bot holatini nazorat qilish

## 🚨 **XATOLIKLAR VA YECHIMLARI**

### **Umumiy xatoliklar:**
- **Telegram Conflict Error** - Bir nechta bot instance
- **Database connection error** - Bazaga ulanish muammosi
- **Content topilmadi** - Noto'g'ri hashtag yoki o'qituvchi

### **Yechimlar:**
- Barcha bot jarayonlarini to'xtatish
- Database ni tekshirish
- Hashtag formatlarini tekshirish

## 🎯 **KELGUSI RIVOJLANISH**

### **Rejalashtirilgan funktsiyalar:**
- Voice message qo'llab-quvvatlash
- Video kontent qo'llab-quvvatlash
- Quiz natijalarini saqlash
- Progress tracking
- Certificate generatsiya

### **Imkoniyatlar:**
- Ko'proqa o'qituvchilar qo'shish
- Boshqa tillarni qo'llab-quvvatlash
- Web interfeys yaratish
- Mobile app integratsiya

---

## 📞 **ALOQA**

**Bot Token:** 8479744985:AAFUCKSUrxzQ8rUWO2WcLnrop_mWqN4KOPo
**Admin ID:** 5964436818
**Asosiy Kanal:** https://t.me/cefrtest1

---

**Bot Version:** 2.0 (Optimized Version)
**Last Update:** 2026-03-12
**Status:** ✅ Active and Working
