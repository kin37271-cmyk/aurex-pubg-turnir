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

from config import BOT_TOKEN, ADMIN_IDS, CHANNEL_ID, get_webapp_url, set_webapp_url
from database import init_db
from handlers import user_router, admin_router
from webapp import start_webapp_server
from utils import CloudflareTunnelManager

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

    # Cloudflare Tunnelni boshqarish
    tunnel_mgr = None
    active_url = get_webapp_url()
    auto_tunnel_env = os.getenv("AUTO_TUNNEL", "true").lower()

    if auto_tunnel_env in ("true", "1", "yes"):
        # Agar WEBAPP_URL bo'sh bo'lsa yoki trycloudflare bo'lsa, avtomatik tunnel ochish
        is_trycloudflare = (not active_url) or ("trycloudflare.com" in active_url)
        if is_trycloudflare:
            tunnel_mgr = CloudflareTunnelManager(port=web_port)
            if tunnel_mgr.is_available():
                tunnel_url = await tunnel_mgr.start()
                if tunnel_url:
                    set_webapp_url(tunnel_url)
                    active_url = tunnel_url

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
    if active_url and active_url.startswith("https://"):
        try:
            await aiogram_bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🎮 AUREX TURNIR",
                    web_app=WebAppInfo(url=active_url)
                )
            )
            logger.info(f"📱 Web App Menu tugmasi sozlandi: {active_url}")
        except Exception as e:
            logger.warning(f"Menu tugmasini sozlashda ogohlantirish: {e}")

    # Handlerlarni ulash
    dp.include_router(admin_router)
    dp.include_router(user_router)

    bot_info = await aiogram_bot.get_me()
    print("\n" + "=" * 60)
    print("🏆  AUREX PUBG MOBILE TURNIR BOTI VA WEB APP ISHGA TUSHDI!  🏆")
    print("=" * 60)
    print(f"🤖 Telegram Bot:   @{bot_info.username}")
    print(f"🌐 Web App URL:    {active_url or 'Sozlanmagan'}")
    print(f"🛡️ Adminlar soni:  {len(ADMIN_IDS)}")
    print(f"📢 Kanal:          {CHANNEL_ID or 'Sozlanmagan'}")
    print("=" * 60 + "\n")

    try:
        await dp.start_polling(aiogram_bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if tunnel_mgr:
            await tunnel_mgr.stop()
        await webapp_runner.cleanup()
        await aiogram_bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
