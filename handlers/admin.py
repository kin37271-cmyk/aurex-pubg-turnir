import asyncio
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, CHANNEL_ID, get_webapp_url
from database import (
    get_all_slots,
    get_slot,
    get_tournament,
    update_tournament_stage,
    set_room_details,
    update_slot_price,
    reset_tournament,
    cancel_slot,
    get_registered_players,
    create_schedule,
    get_all_matches,
    get_stats
)
from keyboards import (
    get_admin_panel_inline,
    get_confirm_reset_inline,
    get_channel_button,
    get_main_menu,
    get_cancel_menu
)
from states import AdminStates
from utils import format_channel_post, format_schedule_text, get_final_fireworks_text

router = Router()

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
@router.message(F.text == "🛡️ Admin Panel")
async def cmd_admin_panel(message: Message, state: FSMContext):
    """Admin boshqaruv paneli"""
    await state.clear()
    if not is_admin(message.from_user.id):
        return

    stats = await get_stats()
    tournament = await get_tournament()
    title = tournament.get("title", "Aurex PUBG Mobile Turniri")
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    start_date = tournament.get("start_date") or "Belgilanmagan"
    slot_price = tournament.get("slot_price") or 0
    price_str = f"{slot_price:,} so'm" if slot_price > 0 else "BEPUL / TEKIN"
    room_id = tournament.get("room_id") or "Kiritilmagan"
    room_pass = tournament.get("room_password") or "Kiritilmagan"

    text = (
        f"🛡️ <b>AUREX PUBG ADMIN BOSHQARUV PANELI</b>\n\n"
        f"🏆 <b>Turnir:</b> {title}\n"
        f"📍 <b>Hozirgi Bosqich:</b> {stage_name}\n"
        f"💵 <b>Slot narxi:</b> <b>{price_str}</b>\n"
        f"📅 <b>Boshlanish sanasi:</b> {start_date}\n"
        f"👥 <b>Yig'ilgan odam:</b> {stats['booked_slots']}/16 ta\n"
        f"🎮 <b>Rejalashtirilgan o'yinlar:</b> {stats['total_matches']} ta (Har 2 kunda 2 ta)\n"
        f"🚪 <b>Hozirgi Room ID:</b> <code>{room_id}</code>\n"
        f"🔑 <b>Hozirgi Parol:</b> <code>{room_pass}</code>\n\n"
        f"Amallardan birini tanlang:"
    )

    await message.answer(text, reply_markup=get_admin_panel_inline())

@router.callback_query(F.data == "admin_open_registration")
async def callback_admin_open_registration(callback: CallbackQuery):
    """Ro'yxatga olish bosqichini qayta ochish"""
    if not is_admin(callback.from_user.id):
        return

    await update_tournament_stage("registration", "Ro'yxatga olish")
    await callback.message.answer(
        "✅ <b>TURNIRGA RO'YXATGA OLISH OCHILDI!</b>\n\n"
        "🎮 Endi barcha ishtirokchilar Bot va Web App orqali erkin slot band qilishlari mumkin.",
        reply_markup=get_main_menu(callback.from_user.id)
    )
    await callback.answer("Ro'yxatga olish ochildi!", show_alert=True)

@router.callback_query(F.data == "admin_post_channel")
async def callback_admin_post_channel(callback: CallbackQuery, bot: Bot):

    """Kanalga odam yig'ish va turnir holati postini yuborish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    if not CHANNEL_ID:
        await callback.answer("⚠️ .env faylida CHANNEL_ID ko'rsatilmagan!", show_alert=True)
        return

    slots = await get_all_slots()
    tournament = await get_tournament()
    title = tournament.get("title", "Aurex PUBG Mobile Turniri")
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    start_date = tournament.get("start_date", "")
    bot_info = await bot.get_me()

    post_text = format_channel_post(
        slots=slots,
        title=title,
        bot_username=bot_info.username,
        stage_name=stage_name,
        start_date=start_date
    )

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_text,
            reply_markup=get_channel_button(bot_info.username, get_webapp_url())
        )

        await callback.answer("✅ Kanalga post muvaffaqiyatli yuborildi!", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Kanalga yuborishda xatolik: {e}", show_alert=True)

@router.callback_query(F.data == "admin_list_players")
async def callback_admin_list_players(callback: CallbackQuery):
    """16 ta slotdagi o'yinchilarning PUBG ID va kontakt ma'lumotlari"""
    if not is_admin(callback.from_user.id):
        return

    slots = await get_all_slots()
    booked_count = sum(1 for s in slots if s.get("user_id"))
    lines = [f"📋 <b>16 TA ISHTIROKCHI RO'YXATI ({booked_count}/16 ta odam yig'ildi):</b>\n"]

    for s in slots:
        num = s["slot_number"]
        if s.get("user_id"):
            nick = s.get("pubg_nick") or "Noma'lum"
            pubg_id = s.get("pubg_id") or "---"
            user_name = s.get("user_name") or "Ismsiz"
            tg_username = f"@{s['user_username']}" if s.get("user_username") else "yo'q"
            phone = s.get("phone") or "yo'q"
            user_id = s.get("user_id")

            lines.append(
                f"<b>[Slot #{num:02d}]</b> 🔴 <b>{nick}</b>\n"
                f" ├ <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
                f" ├ <b>Telegram:</b> {user_name} ({tg_username})\n"
                f" ├ <b>TG ID:</b> <code>{user_id}</code>\n"
                f" └ <b>Tel:</b> {phone}\n"
            )
        else:
            lines.append(f"<b>[Slot #{num:02d}]</b> 🟢 <i>Bo'sh o'rin</i>\n")

    full_text = "\n".join(lines)
    if len(full_text) > 4000:
        for x in range(0, len(full_text), 4000):
            await callback.message.answer(full_text[x:x+4000])
    else:
        await callback.message.answer(full_text)
        
    await callback.answer()

@router.callback_query(F.data == "admin_start_tournament")
async def callback_admin_start_tournament(callback: CallbackQuery, state: FSMContext):
    """Turnirni start qilish (Har 2 kunda 2 ta o'yin)"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_start_date)
    today_str = datetime.now().strftime("%d-%m-%Y")
    await callback.message.answer(
        f"🚀 <b>TURNIRNI START QILISH VA JADVAL TUZISH</b>\n\n"
        f"O'yinlar qoidasi: <b>Har 2 kunda 2 ta o'yin</b> PUBG Mobile Custom Room'da o'tkaziladi!\n\n"
        f"Turnirning 1-o'yin kunini kiriting (masalan: <code>{today_str}</code> yoki 'bugun'):",
        reply_markup=get_cancel_menu()
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext, bot: Bot):
    """Boshlanish sanasini saqlash va jadvalni yaratish"""
    raw_date = message.text.strip().lower()
    
    if raw_date == "bugun":
        start_dt = datetime.now()
    else:
        try:
            # Format: DD-MM-YYYY yoki DD.MM.YYYY
            normalized = raw_date.replace(".", "-").replace("/", "-")
            start_dt = datetime.strptime(normalized, "%d-%m-%Y")
        except ValueError:
            await message.answer("⚠️ Sana formati noto'g'ri. Masalan: <code>28-09-2026</code> yoki <code>bugun</code> deb yozing:")
            return

    await state.clear()
    start_date_str = start_dt.strftime("%d-%m-%Y")

    # Jadvalni generatsiya qilish (Har 2 kunda 2 ta o'yin)
    matches = await create_schedule(start_dt)
    await update_tournament_stage("chorak_final", "Chorak final", start_date=start_date_str)

    schedule_text = format_schedule_text(matches, start_date=start_date_str)

    # 16 ta ishtirokchiga jadvalni yuborish
    registered = await get_registered_players()
    notify_text = (
        f"🚀 <b>TURNIR BOSHLANDI VA O'YINLAR JADVALI TAYYOR!</b>\n\n"
        f"Hurmatli o'yinchi, o'yinlar PUBG Mobile ilovasida Custom Room orqali bo'ladi.\n"
        f"Tartib: <b>Har 2 kunda 2 ta o'yin</b> (20:00 va 21:00 da)!\n\n"
        f"{schedule_text}\n\n"
        f"Har bir o'yin oldidan xona ID va paroli sizga yuboriladi. Tayyor bo'ling! ⚔️"
    )

    sent = 0
    for p in registered:
        try:
            await bot.send_message(chat_id=p["user_id"], text=notify_text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    # Kanalga post qilish
    if CHANNEL_ID:
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📢 <b>AUREX PUBG TURNIR JADVALI E'LON QILINDI!</b>\n\n{schedule_text}"
            )
        except Exception:
            pass

    await message.answer(
        f"✅ <b>TURNIR START OLDI!</b>\n\n"
        f"📅 Boshlanish sanasi: <b>{start_date_str}</b>\n"
        f"🎮 Jadval tuzildi: <b>Har 2 kunda 2 ta o'yin</b>\n"
        f"📬 <b>{sent} ta</b> ishtirokchiga jadval yetkazildi va kanalga joylandi!",
        reply_markup=get_main_menu(message.from_user.id)
    )

@router.callback_query(F.data == "admin_announce_quarter")
async def callback_announce_quarter(callback: CallbackQuery, bot: Bot):
    """Chorak final e'lonini barcha ishtirokchilarga va kanalga chiqarish"""
    if not is_admin(callback.from_user.id):
        return

    await update_tournament_stage("chorak_final", "Chorak final")
    matches = await get_all_matches()
    tournament = await get_tournament()
    start_date = tournament.get("start_date", "")

    quarter_text = (
        "⚔️ <b>DIQQAT! AUREX PUBG TURNIR - CHORAK FINAL!</b> ⚔️\n\n"
        "16 nafar sara o'yinchilar ishtirokidagi Chorak final bahslari boshlanmoqda!\n\n"
        "🎮 <b>O'yin joyi:</b> PUBG Mobile Custom Room\n"
        "⏱ <b>Tartib:</b> Har 2 kunda 2 ta o'yin (20:00 va 21:00)\n\n"
        f"{format_schedule_text(matches, start_date)}\n\n"
        "🔥 Barcha ishtirokchilarga zafar tilaymiz! O'z slotingizda o'ynashni unutmang!"
    )

    # O'yinchilarga tarqatish
    registered = await get_registered_players()
    sent = 0
    for p in registered:
        try:
            await bot.send_message(chat_id=p["user_id"], text=quarter_text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    # Kanalga tarqatish
    if CHANNEL_ID:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=quarter_text)
        except Exception:
            pass

    await callback.message.answer(
        f"✅ <b>Chorak final e'loni {sent} ta ishtirokchiga va kanalga yuborildi!</b>",
        reply_markup=get_main_menu(callback.from_user.id)
    )
    await callback.answer("Chorak final e'lon qilindi!")

@router.callback_query(F.data == "admin_trigger_final")
async def callback_admin_trigger_final(callback: CallbackQuery, state: FSMContext):
    """Final bosqichini boshlash yoki Final salyut animatsiyasini yuborish"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_final_winner)
    await callback.message.answer(
        "🎆 <b>GRAND FINAL VA SALYUT ANIMATSIYASI</b> 🎆\n\n"
        "Turnir qoidasiga ko'ra <b>FAQAT 1-O'RIN (YAGONA CHEMPION)</b> bo'ladi! Kill hisoblanmaydi.\n\n"
        "Finalda Top-1 bo'lgan g'olibning <b>PUBG Nickname</b>'ini kiriting (masalan: <code>AurexPro</code>):",
        reply_markup=get_cancel_menu()
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_final_winner)
async def process_final_fireworks(message: Message, state: FSMContext, bot: Bot):
    """Final natijalarini salyut animatsiyasi bilan tarqatish"""
    winner_nick = message.text.strip()
    await state.clear()

    tournament = await get_tournament()
    title = tournament.get("title", "Aurex PUBG Mobile Turniri")
    await update_tournament_stage("final", "🏆 GRAND FINAL (Taqdirlash)")

    winner_text = (
        f"👑 <b>MUTLAQ G'OLIB (1-O'RIN):</b> <b>{winner_nick}</b> 🏆\n\n"
        f"🎯 <b>Natija:</b> Top-1 Winner Winner Chicken Dinner!\n"
        f"ℹ️ <i>Eslatma: Turnirda kill hisoblanmadi, faqat 1-o'rin g'olib deb topildi!</i>"
    )

    fireworks_post = get_final_fireworks_text(title=title, winner_info=winner_text)

    # 1. Barcha ro'yxatdan o'tgan o'yinchilarga salyut animatsiyasi bilan yuborish
    registered = await get_registered_players()
    sent_count = 0

    status_msg = await message.answer(
        "🎆 <b>Salyutlar otilmoqda va barchaga jo'natilmoqda...</b>",
        reply_markup=get_main_menu(message.from_user.id)
    )

    for p in registered:
        user_id = p["user_id"]
        try:
            # Animatsion emojilar / salyut xabari
            await bot.send_message(chat_id=user_id, text=fireworks_post)
            # Telegram animatsiyasi (salyut/zarba)
            await bot.send_dice(chat_id=user_id, emoji="🎯")
            sent_count += 1
            await asyncio.sleep(0.08)
        except Exception:
            pass

    # 2. Kanalga salyut va final postini yuborish
    channel_status = "Kanalga yuborilmadi"
    if CHANNEL_ID:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=fireworks_post)
            await bot.send_dice(chat_id=CHANNEL_ID, emoji="🎯")
            channel_status = "Kanalga salyut bilan yuborildi ✅"
        except Exception as e:
            channel_status = f"Kanalga yuborishda xato: {e}"

    await status_msg.edit_text(
        f"🎆🎇 <b>GRAND FINAL SALYUT ANIMATSIYASI YUBORILDI!</b> 🎇🎆\n\n"
        f"📬 Ishtirokchilar: <b>{sent_count} ta</b> kishiga yetkazildi!\n"
        f"📢 Kanal holati: <b>{channel_status}</b>\n\n"
        f"Turnir muvaffaqiyatli yakunlandi! 🏆"
    )

@router.callback_query(F.data == "admin_send_room")
async def callback_admin_send_room(callback: CallbackQuery, state: FSMContext):
    """Custom Room ma'lumotlarini kiritish"""
    if not is_admin(callback.from_user.id):
        return

    registered = await get_registered_players()
    if not registered:
        await callback.answer("⚠️ Hozircha hech kim ro'yxatdan o'tmagan!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_room_id)
    await callback.message.answer(
        f"🚪 <b>PUBG MOBILE CUSTOM ROOM OCHILDI</b>\n\n"
        f"Hozirda ro'yxatdan o'tganlar: <b>{len(registered)} ta</b>.\n\n"
        f"PUBG Mobile'dagi <b>Room ID</b> sini kiriting:",
        reply_markup=get_cancel_menu()
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_room_id)
async def process_room_id(message: Message, state: FSMContext):
    """Room ID qabul qilish"""
    room_id = message.text.strip()
    await state.update_data(room_id=room_id)
    await state.set_state(AdminStates.waiting_for_room_pass)
    await message.answer(
        f"✅ Room ID: <code>{room_id}</code>\n\n"
        f"Endi xona <b>Parolini (Password)</b> kiriting:",
        reply_markup=get_cancel_menu()
    )

@router.message(AdminStates.waiting_for_room_pass)
async def process_room_pass(message: Message, state: FSMContext, bot: Bot):
    """Room ID va Parolni 16 ta o'yinchiga tarqatish"""
    room_pass = message.text.strip()
    data = await state.get_data()
    room_id = data.get("room_id")
    await state.clear()

    await set_room_details(room_id, room_pass)

    registered = await get_registered_players()
    sent_count = 0
    fail_count = 0

    status_msg = await message.answer(
        f"🚀 <b>Xona ma'lumotlari barcha 16 o'yinchiga tarqatilmoqda...</b>",
        reply_markup=get_main_menu(message.from_user.id)
    )

    for player in registered:
        user_id = player["user_id"]
        slot_num = player["slot_number"]
        nick = player.get("pubg_nick", "O'yinchi")

        player_text = (
            f"🚨 <b>DIQQAT! PUBG MOBILE XONASI OCHILDI!</b> 🚨\n\n"
            f"Hurmatli <b>{nick}</b>, sizning o'yinga kirish ma'lumotlaringiz:\n\n"
            f"🚪 <b>Room ID:</b> <code>{room_id}</code>\n"
            f"🔑 <b>Parol:</b> <code>{room_pass}</code>\n"
            f"📍 <b>Sizning slotingiz:</b> Slot #{slot_num:02d}\n\n"
            f"⚠️ <b>MUHIM QOIDA:</b>\n"
            f"PUBG Mobile xonasiga kirgach, FAQAT <b>Slot #{slot_num:02d}</b> ga o'tiring! "
            f"Boshqa o'yinchining slotiga o'tirish qat'iyan taqiqlanadi!\n\n"
            f"⏱ Xona 10 daqiqadan so'ng start oladi! Omad!"
        )

        try:
            await bot.send_message(chat_id=user_id, text=player_text)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"✅ <b>XONA MA'LUMOTLARI YUBORILDI!</b>\n\n"
        f"🚪 <b>Room ID:</b> <code>{room_id}</code>\n"
        f"🔑 <b>Parol:</b> <code>{room_pass}</code>\n\n"
        f"📬 Yetkazildi: <b>{sent_count} ta</b> ishtirokchiga\n"
        f"❌ Bloklangan: <b>{fail_count} ta</b>"
    )

@router.callback_query(F.data == "admin_kick_player")
async def callback_admin_kick(callback: CallbackQuery, state: FSMContext):
    """O'yinchini chetlatish"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_kick_slot)
    await callback.message.answer(
        "❌ <b>O'yinchini slotdan chetlatish</b>\n\n"
        "Chiqarib yubormoqchi bo'lgan <b>slot raqamini (1-16)</b> yozing:",
        reply_markup=get_cancel_menu()
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_kick_slot)
async def process_kick_slot(message: Message, state: FSMContext, bot: Bot):
    """Slot bo'yicha kick qilish"""
    text = message.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 16):
        await message.answer("⚠️ Slot raqami 1 dan 16 gacha bo'lishi kerak. Qaytadan kiriting:")
        return

    slot_num = int(text)
    slot = await get_slot(slot_num)
    await state.clear()

    if not slot or not slot.get("user_id"):
        await message.answer(
            f"⚠️ Slot #{slot_num} da hech kim yo'q!",
            reply_markup=get_main_menu(message.from_user.id)
        )
        return

    kicked_user_id = slot["user_id"]
    kicked_nick = slot.get("pubg_nick", "O'yinchi")

    await cancel_slot(slot_num)

    try:
        await bot.send_message(
            chat_id=kicked_user_id,
            text=f"⚠️ <b>DIQQAT:</b> Siz administrator tomonidan <b>Slot #{slot_num:02d}</b> dan chetlatildingiz."
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Slot #{slot_num:02d}</b> dagi o'yinchi (<b>{kicked_nick}</b>) chetlatildi va slot bo'shatildi!",
        reply_markup=get_main_menu(message.from_user.id)
    )

@router.callback_query(F.data == "admin_reset_tournament")
async def callback_admin_reset(callback: CallbackQuery):
    """Turnirni tozalash so'rovi"""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.answer(
        "⚠️ <b>DIQQAT! ROSTAN HAM TURNIRNI TOZALAMOQCHIMISIZ?</b>\n\n"
        "Bu amal barcha 16 ta slotni va o'yinlar jadvalini tozalab, yangi turnirga tayyorlaydi!",
        reply_markup=get_confirm_reset_inline()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_reset_tournament")
async def callback_confirm_reset(callback: CallbackQuery):
    """Turnirni tozalashni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        return

    await reset_tournament()
    await callback.message.edit_text(
        "🔄 <b>TURNIR MUVAFFAQIYATLI TOZALANDI!</b>\n\n"
        "Barcha 16 ta slot bo'shatildi. Yangi turnir uchun ro'yxatga olish boshlandi."
    )
    await callback.answer("Turnir tozalandi!")

@router.callback_query(F.data == "cancel_admin_action")
async def callback_cancel_admin(callback: CallbackQuery):
    """Bekor qilish"""
    await callback.message.delete()
    await callback.answer("Amal bekor qilindi.")

@router.callback_query(F.data == "admin_change_price")
async def callback_admin_change_price(callback: CallbackQuery, state: FSMContext):
    """Slot narxini o'zgartirishni so'rash"""
    if not is_admin(callback.from_user.id):
        return

    tournament = await get_tournament()
    current_price = tournament.get("slot_price") or 0
    curr_str = f"{current_price:,} so'm" if current_price > 0 else "BEPUL"

    await state.set_state(AdminStates.waiting_for_slot_price)
    await callback.message.answer(
        f"💵 <b>SLOT NARXINI O'ZGARTIRISH</b>\n\n"
        f"Hozirgi narx: <b>{curr_str}</b>\n\n"
        f"Yangi slot narxini raqamda kiriting (masalan: <code>20000</code> yoki tekin qilish uchun <code>0</code>):",
        reply_markup=get_cancel_menu()
    )
    await callback.answer()

@router.message(AdminStates.waiting_for_slot_price)
async def process_slot_price(message: Message, state: FSMContext):
    """Yangi slot narxini saqlash"""
    text = message.text.strip().replace(" ", "").replace(",", "").replace(".", "")
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqam kiriting (masalan: <code>25000</code> yoki <code>0</code>):")
        return

    new_price = int(text)
    await update_slot_price(new_price)
    await state.clear()

    price_label = f"{new_price:,} so'm" if new_price > 0 else "BEPUL / TEKIN"
    await message.answer(
        f"✅ <b>Slot narxi muvaffaqiyatli o'zgartirildi!</b>\n\n"
        f"💵 Yangi narx: <b>{price_label}</b>\n"
        f"Ushbu narx Web App va botda darhol aks etadi.",
        reply_markup=get_main_menu(message.from_user.id)
    )
