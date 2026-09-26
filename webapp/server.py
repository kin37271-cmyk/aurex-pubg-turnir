import os
from aiohttp import web
from database import (
    get_tournament,
    get_all_slots,
    get_slot,
    get_all_matches,
    book_slot,
    cancel_slot
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
            return web.json_response({"success": False, "error": "Bu slot allaqachon band qilingan yoki siz oldin slot olgansiz"}, status=400)

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
    app.router.add_post("/api/book", api_book_slot)

    return app

async def start_webapp_server(host: str = "0.0.0.0", port: int = 8080):
    """Web serverni asyncio ichida fonda ishga tushirish"""
    app = create_webapp()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner
