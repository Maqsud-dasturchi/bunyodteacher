# Kanal skanerlash testi

Agar bot kanalga admin qilib o'rnatilgan bo'lsa, u kanaldagi barcha o'tmish xabarlarni o'qib oladi va ularni database ga saqlashi mumkin.

## Mavjud muammo:
Bot kanaldan xabarlarni o'qiy olmayapti, chunki:
1. Bot kanalga admin emas
2. Aiogram versiyasi mos kelmayapti
3. API cheklovlari

## Yechim variantlari:

### 1. Botni kanalga admin qilish
- Botni kanalga admin sifatida qo'shing
- Botga kanalni o'qish huquqi bering

### 2. Faqat yangi xabarlarni qabul qilish
- Bot faqat yangi keladigan xabarlarni qayta ishlaydi
- O'tmishdagi kontentni qo'lda yuklash kerak

### 3. To'g'ri aiogram metodi
```python
# Aiogram 3.x uchun to'g'ri usul
from aiogram import types
from aiogram.methods import GetChatHistory

# Kanaldan xabarlarni olish
history = await bot(GetChatHistory(
    chat_id=channel_id,
    limit=100,
    offset_id=0
))
```

## Hozirgi holat:
Bot kanaldan yangi xabarlarni qabul qiladi va ularni saqlashi kerak.
Ammo saqlash jarayonida muammo bor.

## Tavsiya:
1. Botni kanalga admin qiling
2. Kanaldan test xabar yuboring
3. Saqlanishini tekshiring
4. Agar saqlanmasa, database.save_content funksiyasini tekshiring
