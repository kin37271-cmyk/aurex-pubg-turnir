import os
from aiohttp import web
from config import ADMIN_IDS
from database import (
    get_tournament,
    get_all_slots,
    get_slot,
    get_user_slot,
    get_all_matches,
    get_registered_players,
    book_slot,
    cancel_slot,
    set_room_details,
    update_tournament_stage,
    update_slot_price,
    reset_tournament
)

WEBAPP_DIR = os.path.dirname(os.path.abspath(__file__))

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
    """Turnir ma'lumotlarini qaytarish"""
    data = await get_tournament()
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

async def api_book_slot(request):
    """Slotni band qilish API"""
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

        # Slot holatini tekshirish
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

        # Agar admin bo'lsa to'g'ridan to'g'ri bo'shata oladi
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

# --- ADMIN API ENDPOINTS ---

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


def create_webapp():
    """aiohttp web dasturini yaratish"""
    app = web.Application()
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
    app.router.add_post("/api/cancel_slot", api_cancel_slot)

    # Admin APIs
    app.router.add_post("/api/admin/room", api_admin_room)
    app.router.add_post("/api/admin/stage", api_admin_stage)
    app.router.add_post("/api/admin/price", api_admin_price)
    app.router.add_post("/api/admin/kick", api_admin_kick)
    app.router.add_post("/api/admin/reset", api_admin_reset)

    return app

async def start_webapp_server(host: str = "0.0.0.0", port: int = 8080):
    """Web serverni asyncio ichida fonda ishga tushirish"""
    app = create_webapp()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner
