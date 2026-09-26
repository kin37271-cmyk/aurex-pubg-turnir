from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from config import ADMIN_IDS, get_webapp_url

def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    """Asosiy foydalanuvchi menyusi"""
    buttons = []
    
    # Agar WEBAPP_URL sozlangan bo'lsa, birinchi qatorda katta Web App tugmasi
    webapp_url = get_webapp_url()
    if webapp_url and webapp_url.startswith("https://"):
        buttons.append([KeyboardButton(text="🚀 TURNIR WEB APP (16/16) 🎮", web_app=WebAppInfo(url=webapp_url))])

    
    buttons.append([KeyboardButton(text="🎮 Turnirga qatnashish"), KeyboardButton(text="📋 16 ta Ishtirokchi")])
    buttons.append([KeyboardButton(text="🗓 O'yinlar jadvali"), KeyboardButton(text="👤 Mening slotim")])
    buttons.append([KeyboardButton(text="ℹ️ Qoidalar")])
    
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="🛡️ Admin Panel")])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Aurex PUBG Turniri menyusi..."
    )

def get_cancel_menu() -> ReplyKeyboardMarkup:
    """Bekor qilish menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def get_phone_menu() -> ReplyKeyboardMarkup:
    """Telefon raqam yuborish menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)],
            [KeyboardButton(text="⏭ O'tkazib yuborish"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
