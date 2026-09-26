from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_slots_grid(slots: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """16 ta slotni 4x4 panjarada ko'rsatish"""
    keyboard = []
    row = []
    
    for s in slots:
        num = s["slot_number"]
        is_booked = bool(s.get("user_id"))
        
        status_icon = "🔴" if is_booked else "🟢"
        text = f"{status_icon} Slot {num:02d}"
        callback = f"select_slot:{num}"
        
        row.append(InlineKeyboardButton(text=text, callback_data=callback))
        if len(row) == 4:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    keyboard.append([
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_slots")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_my_slot_actions(slot_number: int) -> InlineKeyboardMarkup:
    """O'yinchi o'z sloti uchun harakatlar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Slotni bekor qilish", callback_data=f"cancel_slot:{slot_number}")],
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_my_slot")]
    ])

def get_admin_panel_inline() -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Ro'yxatga olishni ochish (Open)", callback_data="admin_open_registration"),
            InlineKeyboardButton(text="🚀 O'yinni start qilish", callback_data="admin_start_tournament")
        ],

        [
            InlineKeyboardButton(text="⚔️ Chorak final e'loni", callback_data="admin_announce_quarter"),
            InlineKeyboardButton(text="🏆 FINAL & SALYUT 🎆", callback_data="admin_trigger_final")
        ],
        [
            InlineKeyboardButton(text="🔑 Room ID & Parol tarqatish", callback_data="admin_send_room"),
            InlineKeyboardButton(text="📢 Kanalga post (Odam yig'ish)", callback_data="admin_post_channel")
        ],
        [
            InlineKeyboardButton(text="📋 16 ta o'yinchi (PUBG ID)", callback_data="admin_list_players"),
            InlineKeyboardButton(text="❌ O'yinchini chetlatish (Kick)", callback_data="admin_kick_player")
        ],
        [
            InlineKeyboardButton(text="💵 Slot narxini o'zgartirish", callback_data="admin_change_price"),
            InlineKeyboardButton(text="🔄 Turnirni tozalash (Reset)", callback_data="admin_reset_tournament")
        ]
    ])

def get_webapp_inline_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    """Foydalanuvchini Web App ga yo'naltiruvchi yagona AUREX TURNIR tugmasi"""
    from aiogram.types import WebAppInfo
    if webapp_url and webapp_url.startswith("https://"):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 AUREX TURNIR", web_app=WebAppInfo(url=webapp_url))]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 AUREX TURNIR", url=webapp_url or "https://t.me")]
    ])

def get_confirm_reset_inline() -> InlineKeyboardMarkup:
    """Turnirni tozalashni tasdiqlash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, barchasini tozalash!", callback_data="confirm_reset_tournament"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin_action")
        ]
    ])

def get_channel_button(bot_username: str, webapp_url: str = "") -> InlineKeyboardMarkup:
    """Kanal posti ostidagi Web App tugmasi"""
    from aiogram.types import WebAppInfo
    if webapp_url:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Turnirga yozilish (Web App)", web_app=WebAppInfo(url=webapp_url))]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Turnirga yozilish (Bot)", url=f"https://t.me/{bot_username}")]
    ])
