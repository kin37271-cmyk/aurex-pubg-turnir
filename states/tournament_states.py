from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_pubg_nick = State()
    waiting_for_pubg_id = State()
    waiting_for_phone = State()

class AdminStates(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_room_id = State()
    waiting_for_room_pass = State()
    waiting_for_kick_slot = State()
    waiting_for_final_winner = State()
    waiting_for_slot_price = State()
