from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from config import get_webapp_url

def get_main_menu(user_id: int = 0) -> ReplyKeyboardMarkup:
    """Asosiy menyu - Faqat AUREX TURNIR Web App tugmasi"""
    webapp_url = get_webapp_url()
    if webapp_url and webapp_url.startswith("https://"):
        btn = KeyboardButton(text="🎮 AUREX TURNIR", web_app=WebAppInfo(url=webapp_url))
    else:
        btn = KeyboardButton(text="🎮 AUREX TURNIR")

    return ReplyKeyboardMarkup(
        keyboard=[[btn]],
        resize_keyboard=True,
        input_field_placeholder="Web App ga kirish uchun tugmani bosing..."
    )

def get_cancel_menu() -> ReplyKeyboardMarkup:
    """Bekor qilish menyusi"""
    return get_main_menu()
