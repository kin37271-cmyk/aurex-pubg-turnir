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

# To'lov cheklari boradigan asosiy Admin (8825408278)
PAYMENT_ADMIN_ID = int(os.getenv("PAYMENT_ADMIN_ID", "8825408278"))

# To'lov kartasi ma'lumotlari
CARD_HOLDER = os.getenv("CARD_HOLDER", "Murodaliyev Abdulaziz")
CARD_NUMBER = os.getenv("CARD_NUMBER", "4198130083012731")

# Rasmiy kanal username yoki ID si (masalan: @aurex_pubg yoki -1001234567890)
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# Telegram Web App manzili (HTTPS bo'lishi shart)
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

def get_webapp_url() -> str:
    """Hozirgi aktiv Web App manzilini qaytarish"""
    return os.getenv("WEBAPP_URL", WEBAPP_URL)

def set_webapp_url(new_url: str):
    """Web App manzilini yangilash va .env fayliga saqlash"""
    global WEBAPP_URL
    WEBAPP_URL = new_url
    os.environ["WEBAPP_URL"] = new_url
    
    # .env faylini avtomatik yangilash
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            found = False
            new_lines = []
            for line in lines:
                if line.startswith("WEBAPP_URL=") or line.strip() == "WEBAPP_URL":
                    new_lines.append(f"WEBAPP_URL={new_url}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"WEBAPP_URL={new_url}\n")
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            pass

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
