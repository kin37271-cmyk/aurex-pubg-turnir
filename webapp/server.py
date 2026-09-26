import os
import time
import logging
from aiohttp import web
from config import ADMIN_IDS, PAYMENT_ADMIN_ID, CARD_HOLDER, CARD_NUMBER
from database import (
    get_tournament,
    get_all_slots,
    get_slot,
    get_user_slot,
    get_all_matches,
    get_registered_players,
    book_slot,
    book_slot_pending,
    approve_slot,
    cancel_slot,
    set_room_details,
    update_tournament_stage,
    update_slot_price,
    reset_tournament
)

logger = logging.getLogger("AurexServer")
WEBAPP_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPTS_DIR = os.path.join(os.path.dirname(WEBAPP_DIR), "assets", "receipts")
os.makedirs(RECEIPTS_DIR, exist_ok=True)

async def handle_index(request):
    """Bosh sahifani uzatish"""
    return web.FileResponse(os.path.join(WEBAPP_DIR, "index.html"))

async def handle_static_style(request):
    """CSS faylni uzatish"""
    return web.FileResponse(os.path.join(WEBAPP_DIR, "style.css"))

async def handle_static_app(request):
    """JS faylni uzatish"""
    return web.FileResponse(os.path.join(WEBAPP_DIR, "app.js"))

async def api_get_tournament(request):
    """Turnir va to'lov karta ma'lumotlarini qaytarish"""
    data = await get_tournament()
    data["card_holder"] = CARD_HOLDER
    data["card_number"] = CARD_NUMBER
    data["payment_admin_id"] = PAYMENT_ADMIN_ID
    return web.json_response(data)

async def api_get_slots(request):
    """Barcha 16 ta slotni qaytarish"""
    slots = await get_all_slots()
    return web.json_response(slots)

async def api_get_schedule(request):
    """O'yinlar jadvalini qaytarish"""
    matches = await get_all_matches()
    return web.json_response(matches)

async def api_get_players(request):
    """Mijozlar / Ro'yxatdan o'tgan barcha ishtirokchilar ro'yxati"""
    players = await get_registered_players()
    return web.json_response(players)

async def api_get_profile(request):
    """Foydalanuvchi profili va band qilgan sloti"""
    try:
        user_id_str = request.query.get("user_id")
        if not user_id_str:
            return web.json_response({"slot": None})
        user_id = int(user_id_str)
        slot = await get_user_slot(user_id)
        is_admin = user_id in ADMIN_IDS
        return web.json_response({
            "user_id": user_id,
            "is_admin": is_admin,
            "slot": slot
        })
    except Exception as e:
        return web.json_response({"error": str(e), "slot": None}, status=400)

async def api_check_admin(request):
    """Adminlik huquqini tekshirish"""
    try:
        user_id_str = request.query.get("user_id", "0")
        user_id = int(user_id_str)
        return web.json_response({"is_admin": user_id in ADMIN_IDS})
    except Exception:
        return web.json_response({"is_admin": False})

async def api_book_with_receipt(request):
    """Chek bilan birga slotni band qilish API"""
    try:
        data = await request.post()
        slot_number = int(data.get("slot_number", 0))
        user_id = int(data.get("user_id", 0))
        user_name = str(data.get("user_name", "Ishtirokchi"))
        user_username = data.get("user_username")
        pubg_nick = str(data.get("pubg_nick", "")).strip()
        pubg_id = str(data.get("pubg_id", "")).strip()
        phone = str(data.get("phone", "")).strip()

        if not (1 <= slot_number <= 16):
            return web.json_response({"success": False, "error": "Slot raqami 1 dan 16 gacha bo'lishi kerak"}, status=400)

        if not pubg_nick or not pubg_id:
            return web.json_response({"success": False, "error": "PUBG Nickname va PUBG ID to'ldirilishi shart"}, status=400)

        if not phone:
            return web.json_response({"success": False, "error": "Telefon raqamingizni kiriting"}, status=400)

        # Chek faylini olish va saqlash
        receipt_file = data.get("receipt")
        saved_filename = None
        saved_filepath = None

        if receipt_file and hasattr(receipt_file, "file"):
            content = receipt_file.file.read()
            if content:
                ext = ".jpg"
                orig_name = getattr(receipt_file, "filename", "")
                if orig_name and "." in orig_name:
                    ext = "." + orig_name.rsplit(".", 1)[1].lower()
                saved_filename = f"receipt_slot{slot_number}_{user_id}_{int(time.time())}{ext}"
                saved_filepath = os.path.join(RECEIPTS_DIR, saved_filename)
                with open(saved_filepath, "wb") as f:
                    f.write(content)

        if not saved_filepath or not os.path.exists(saved_filepath):
            return web.json_response({"success": False, "error": "Iltimos, to'lov cheki skrinshotini yuklang!"}, status=400)

        # Slot holatini tekshirish
        slot = await get_slot(slot_number)
        if not slot:
            return web.json_response({"success": False, "error": "Slot topilmadi"}, status=404)
        if slot.get("user_id") and slot.get("user_id") != user_id:
            return web.json_response({"success": False, "error": f"Slot #{slot_number} allaqachon band qilingan"}, status=400)

        # Pending statusida band qilish
        success = await book_slot_pending(
            slot_number=slot_number,
            user_id=user_id,
            user_name=user_name,
            user_username=user_username,
            pubg_nick=pubg_nick,
            pubg_id=pubg_id,
            phone=phone,
            receipt_path=saved_filepath
        )

        if not success:
            return web.json_response({"success": False, "error": "Bu slot band yoki siz allaqachon boshqa slot olgansiz"}, status=400)

        # Admin 8825408278 ga Telegram orqali chekni yuborish
        bot = request.app.get("bot")
        if bot:
            from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
            caption = (
                f"🧾 <b>YANGI TO'LOV CHEKI TUSHDI!</b>\n\n"
                f"📍 <b>Slot:</b> Slot #{slot_number:02d}\n"
                f"👤 <b>PUBG Nick:</b> <code>{pubg_nick}</code>\n"
                f"🆔 <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
                f"📱 <b>Telefon:</b> <code>{phone}</code>\n"
                f"👤 <b>Foydalanuvchi:</b> {user_name} (@{user_username or 'yo_q'})\n"
                f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
                f"💰 <b>To'lov:</b> 10 000 so'm (100%)\n"
                f"💳 <b>Karta:</b> <code>{CARD_NUMBER}</code> ({CARD_HOLDER})\n\n"
                f"❓ <b>To'lovni tasdiqlaysizmi?</b>"
            )
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pay_approve:{slot_number}:{user_id}"),
                    InlineKeyboardButton(text="❌ Yo'q (Rad etish)", callback_data=f"pay_reject:{slot_number}:{user_id}")
                ]
            ])
            try:
                await bot.send_photo(
                    chat_id=PAYMENT_ADMIN_ID,
                    photo=FSInputFile(saved_filepath),
                    caption=caption,
                    reply_markup=markup
                )
                logger.info(f"✅ Chek adminga ({PAYMENT_ADMIN_ID}) yuborildi: Slot #{slot_number}")
            except Exception as bot_err:
                logger.error(f"Adminga chek yuborishda xato: {bot_err}")

        return web.json_response({
            "success": True,
            "slot_number": slot_number,
            "message": "To'lov cheki adminga tekshirish uchun yuborildi! Tez orada tasdiqlanadi."
        })

    except Exception as e:
        logger.error(f"api_book_with_receipt xatosi: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_book_slot(request):
    """Oddiy band qilish (bepul bo'lganda)"""
    try:
        body = await request.json()
        slot_number = int(body.get("slot_number", 0))
        user_id = int(body.get("user_id", 0))
        user_name = str(body.get("user_name", "Ishtirokchi"))
        user_username = body.get("user_username")
        pubg_nick = str(body.get("pubg_nick", "")).strip()
        pubg_id = str(body.get("pubg_id", "")).strip()
        phone = body.get("phone")

        if not slot_number or not (1 <= slot_number <= 16):
            return web.json_response({"success": False, "error": "Slot raqami 1 dan 16 gacha bo'lishi kerak"}, status=400)

        if not pubg_nick or not pubg_id:
            return web.json_response({"success": False, "error": "PUBG Nickname va PUBG ID to'ldirilishi shart"}, status=400)

        slot = await get_slot(slot_number)
        if not slot:
            return web.json_response({"success": False, "error": "Slot topilmadi"}, status=404)
        if slot.get("user_id"):
            return web.json_response({"success": False, "error": f"Slot #{slot_number} allaqachon band qilingan"}, status=400)

        success = await book_slot(
            slot_number=slot_number,
            user_id=user_id,
            user_name=user_name,
            user_username=user_username,
            pubg_nick=pubg_nick,
            pubg_id=pubg_id,
            phone=phone
        )

        if success:
            return web.json_response({"success": True, "slot_number": slot_number})
        else:
            return web.json_response({"success": False, "error": "Bu slot band yoki siz oldin slot olgansiz"}, status=400)

    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_cancel_slot(request):
    """Foydalanuvchi o'z slotini bekor qilishi (yoki admin bekor qilishi)"""
    try:
        body = await request.json()
        slot_number = int(body.get("slot_number", 0))
        user_id = int(body.get("user_id", 0))

        if not (1 <= slot_number <= 16):
            return web.json_response({"success": False, "error": "Noto'g'ri slot raqami"}, status=400)

        if user_id in ADMIN_IDS:
            ok = await cancel_slot(slot_number)
        else:
            ok = await cancel_slot(slot_number, user_id=user_id)

        if ok:
            return web.json_response({"success": True, "message": f"Slot #{slot_number} bo'shatildi"})
        else:
            return web.json_response({"success": False, "error": "Slotni bekor qilish imkoni bo'lmadi"}, status=400)
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

# --- ADMIN APIS ---

async def api_admin_room(request):
    """Admin: Xona ID va parolini o'rnatish"""
    try:
        body = await request.json()
        admin_id = int(body.get("admin_id", 0))
        if admin_id not in ADMIN_IDS:
            return web.json_response({"success": False, "error": "Ruxsat etilmagan (Admin huquqi yo'q)"}, status=403)

        room_id = str(body.get("room_id", "")).strip()
        room_password = str(body.get("room_password", "")).strip()

        await set_room_details(room_id, room_password)
        return web.json_response({"success": True, "room_id": room_id, "room_password": room_password})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_stage(request):
    """Admin: Turnir bosqichini o'zgartirish"""
    try:
        body = await request.json()
        admin_id = int(body.get("admin_id", 0))
        if admin_id not in ADMIN_IDS:
            return web.json_response({"success": False, "error": "Ruxsat etilmagan"}, status=403)

        status = body.get("status", "registration")
        stage_name = body.get("stage_name", "Ro'yxatga olish")
        winner_nick = body.get("winner_nick")

        await update_tournament_stage(status=status, stage_name=stage_name, winner_nick=winner_nick)
        return web.json_response({"success": True, "status": status, "stage_name": stage_name})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_price(request):
    """Admin: Slot narxini yangilash"""
    try:
        body = await request.json()
        admin_id = int(body.get("admin_id", 0))
        if admin_id not in ADMIN_IDS:
            return web.json_response({"success": False, "error": "Ruxsat etilmagan"}, status=403)

        price = int(body.get("price", 0))
        await update_slot_price(price)
        return web.json_response({"success": True, "price": price})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_kick(request):
    """Admin: O'yinchini slotdan chetlatish"""
    try:
        body = await request.json()
        admin_id = int(body.get("admin_id", 0))
        if admin_id not in ADMIN_IDS:
            return web.json_response({"success": False, "error": "Ruxsat etilmagan"}, status=403)

        slot_number = int(body.get("slot_number", 0))
        ok = await cancel_slot(slot_number)
        return web.json_response({"success": ok})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_admin_reset(request):
    """Admin: Turnirni tozalash"""
    try:
        body = await request.json()
        admin_id = int(body.get("admin_id", 0))
        if admin_id not in ADMIN_IDS:
            return web.json_response({"success": False, "error": "Ruxsat etilmagan"}, status=403)

        title = body.get("title", "Aurex PUBG Mobile Turniri")
        await reset_tournament(new_title=title)
        return web.json_response({"success": True})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)


def create_webapp(bot=None):
    """aiohttp web dasturini yaratish"""
    app = web.Application()
    app["bot"] = bot

    app.router.add_get("/", handle_index)
    app.router.add_get("/index.html", handle_index)
    app.router.add_get("/static/style.css", handle_static_style)
    app.router.add_get("/static/app.js", handle_static_app)

    # API endpoints
    app.router.add_get("/api/tournament", api_get_tournament)
    app.router.add_get("/api/slots", api_get_slots)
    app.router.add_get("/api/schedule", api_get_schedule)
    app.router.add_get("/api/players", api_get_players)
    app.router.add_get("/api/profile", api_get_profile)
    app.router.add_get("/api/check_admin", api_check_admin)

    app.router.add_post("/api/book", api_book_slot)
    app.router.add_post("/api/book_with_receipt", api_book_with_receipt)
    app.router.add_post("/api/cancel_slot", api_cancel_slot)

    # Admin APIs
    app.router.add_post("/api/admin/room", api_admin_room)
    app.router.add_post("/api/admin/stage", api_admin_stage)
    app.router.add_post("/api/admin/price", api_admin_price)
    app.router.add_post("/api/admin/kick", api_admin_kick)
    app.router.add_post("/api/admin/reset", api_admin_reset)

    return app

async def start_webapp_server(bot=None, host: str = "0.0.0.0", port: int = 8080):
    """Web serverni asyncio ichida fonda ishga tushirish"""
    app = create_webapp(bot=bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner
