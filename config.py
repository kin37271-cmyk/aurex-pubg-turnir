import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin Telegram ID raqamlari (vergul bilan ajratilgan: 1234567,9876543)
admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = [
    int(x.strip()) for x in admin_ids_raw.split(",") if x.strip().isdigit()
]

# Rasmiy kanal username yoki ID si (masalan: @aurex_pubg yoki -1001234567890)
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# Telegram Web App manzili (HTTPS bo'lishi shart)
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

# Turnir qoidalari
DEFAULT_RULES = """
🏆 <b>AUREX PUBG MOBILE TURNIR QOIDALARI</b>

1️⃣ <b>Ishtirokchilar soni:</b> 16 ta o'yinchi (Solo format).
2️⃣ <b>Xonaga kirish:</b> Turnir boshlanishidan 10 daqiqa oldin bot orqali Room ID va Parol yuboriladi.
3️⃣ <b>Slot tartibi:</b> Har bir o'yinchi FAQAT o'zi band qilgan slot raqamiga o'tirishi shart! Boshqa slotga o'tirish = chetlatish (kick).
4️⃣ <b>Taqiqlangan vositalar:</b>
   • Chiterlik, emulyator (PC) va iPad view taqiqlanadi (Faqat telefon/planshet).
   • Teaming (o'zaro kelishib olish) qat'iyan man etiladi.
5️⃣ <b>G'olibni aniqlash:</b> Turnirda FAQAT 1-O'RIN (Top-1 Winner) g'olib bo'ladi! Kill hisoblanmaydi, o'yinda oxirgi tirik qolgan o'yinchi mutlaq chempion deb topiladi!
6️⃣ Natijalar o'yin yakunlangach bot va kanalimizda e'lon qilinadi.

🔥 <i>Barchaga omad tilaymiz! Hurmat bilan, Aurex jamoasi.</i>
"""
