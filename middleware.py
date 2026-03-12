from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from database import db
from config import ADMIN_ID

class BlockingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event,
        data
    ):
        # Adminni tekshirmaymiz
        user_id = event.from_user.id
        if user_id == ADMIN_ID:
            return await handler(event, data)

        # Bloklanganligini tekshirish
        if db.is_user_blocked(user_id):
            if isinstance(event, Message):
                await event.answer(
                    "⛔️ Kechirasiz, siz admin tomonidan bloklangansiz.",
                    reply_markup=ReplyKeyboardRemove()
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "⛔️ Kechirasiz, siz admin tomonidan bloklangansiz.",
                    show_alert=True
                )
                # Xabarni o'chirishga urinib ko'ramiz (menyuni yo'qotish uchun)
                try:
                    await event.message.delete()
                except:
                    pass
            
            # Eventni to'xtatish (keyingi handlerlarga o'tmaydi)
            return

        # Agar bloklanmagan bo'lsa, davom etamiz
        return await handler(event, data)
