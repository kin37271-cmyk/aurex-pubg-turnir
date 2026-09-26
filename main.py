import asyncio
import logging
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from config import BOT_TOKEN, ADMIN_IDS, CHANNEL_ID, WEBAPP_URL
from database import init_db
from handlers import user_router, admin_router
from webapp import start_webapp_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AurexPubgBot")

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error(
            "❌ DIQQAT: BOT_TOKEN ko'rsatilmagan!\n"
            "Iltimos, '.env' fayliga BotFather'dan olingan tokeningizni kiriting."
        )
        return

    # Ma'lumotlar bazasini ishga tushirish
    logger.info("📦 Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()
    logger.info("✅ Ma'lumotlar bazasi tayyor!")

    # Web App serverini ishga tushirish
    web_port = int(os.getenv("PORT", "8080"))
    logger.info(f"🌐 Web App server ishga tushirilmoqda (port {web_port})...")
    webapp_runner = await start_webapp_server(host="0.0.0.0", port=web_port)
    logger.info(f"✅ Web App server tayyor: http://localhost:{web_port}")

    bot = DefaultBotProperties(parse_mode=ParseMode.HTML)
    aiogram_bot = Bot(token=BOT_TOKEN, default=bot)
    dp = Dispatcher(storage=MemoryStorage())

    # Botning Tavsifi (Description) va Bio (Short Description) sozlash
    try:
        await aiogram_bot.set_my_description(
            description=(
                "🏆 AUREX PUBG MOBILE TURNIR BOTI & WEB APP\n\n"
                "🎮 16 kishilik maxsus PUBG Mobile Custom Room turnirlari.\n"
                "⏱ O'yinlar har 2 kunda 2 ta o'yin tartibida o'tkaziladi.\n"
                "👑 Faqat 1-O'rin (Top-1 Winner) — kill hisoblanmaydi!\n"
                "🚪 Xona ID va Parol faqat 16 ishtirokchiga shaxsiy yuboriladi.\n\n"
                "Turnirga qatnashish va slot band qilish uchun /start bosing!"
            )
        )
        await aiogram_bot.set_my_short_description(
            short_description="🏆 Aurex PUBG Mobile 16 Kishilik Turnir Boshqaruvchi Boti & Web App 🎮"
        )
        logger.info("📝 Bot tavsifi (description) va Bio muvaffaqiyatli sozlandi!")
    except Exception as e:
        logger.warning(f"Bot tavsifini sozlashda xato: {e}")

    # Telegram Menu tugmasini sozlash (Web App uchun)
    if WEBAPP_URL and WEBAPP_URL.startswith("https://"):
        try:
            await aiogram_bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🎮 Turnir Web App",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            )
            logger.info(f"📱 Web App Menu tugmasi sozlandi: {WEBAPP_URL}")
        except Exception as e:
            logger.warning(f"Menu tugmasini sozlashda ogohlantirish: {e}")

    # Handlerlarni ulash
    dp.include_router(admin_router)
    dp.include_router(user_router)

    bot_info = await aiogram_bot.get_me()
    logger.info(f"🚀 Aurex PUBG Bot ishga tushdi: @{bot_info.username}")
    logger.info(f"🛡️ Adminlar: {ADMIN_IDS}")
    logger.info(f"📢 Kanal: {CHANNEL_ID or 'Sozlanmagan'}")
    logger.info(f"🌐 Web App URL: {WEBAPP_URL or 'Hali sozlanmagan'}")

    try:
        await dp.start_polling(aiogram_bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await webapp_runner.cleanup()
        await aiogram_bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
