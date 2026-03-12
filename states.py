from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    full_name = State()
    phone = State()
    days = State()
    time = State()
    secret_word = State()

class AdminState(StatesGroup):
    waiting_block_reason = State()
    waiting_block_confirmation = State()
    waiting_unblock_id = State()
    waiting_broadcast_message = State()
    waiting_broadcast_confirmation = State()
