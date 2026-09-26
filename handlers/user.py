from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import (
    get_all_slots,
    get_slot,
    get_user_slot,
    book_slot,
    cancel_slot,
    get_tournament,
    get_all_matches
)
from keyboards import (
    get_main_menu,
    get_cancel_menu,
    get_phone_menu,
    get_slots_grid,
    get_my_slot_actions,
    get_webapp_inline_keyboard
)
from states import RegistrationStates
from utils import format_slots_text, format_schedule_text
from config import DEFAULT_RULES, WEBAPP_URL

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi - to'g'ridan-to'g'ri Web App ga yo'naltirish"""
    await state.clear()
    user_id = message.from_user.id
    name = message.from_user.first_name or "Jangchi"
    
    tournament = await get_tournament()
    title = tournament.get("title", "Aurex PUBG Mobile Turniri")
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    slot_price = tournament.get("slot_price") or 0
    price_str = f"{slot_price:,} so'm" if slot_price > 0 else "BEPUL / TEKIN"

    slots = await get_all_slots()
    booked = sum(1 for s in slots if s.get("user_id"))

    welcome_text = (
        f"👋 Assalomu alaykum, <b>{name}</b>!\n\n"
        f"🏆 <b>{title}</b>\n\n"
        f"🎮 Turnirda qatnashish, 16 ta slotni band qilish, o'yinlar jadvali va PUBG xona ma'lumotlari "
        f"to'liq <b>Aurex Web App</b> da joylashtirilgan!\n\n"
        f"📊 <b>Holat:</b> {booked}/16 ta odam yig'ildi\n"
        f"📍 <b>Bosqich:</b> {stage_name}\n"
        f"💵 <b>Slot narxi:</b> <b>{price_str}</b>\n"
        f"👑 <b>G'olib:</b> Faqat 1-O'rin (Top-1) — kill hisoblanmaydi!\n"
        f"⏱ <b>Tartib:</b> Har 2 kunda 2 ta o'yin (Custom Room)\n\n"
        f"👇 <b>Turnirga kirish uchun pastdagi tugmani bosing:</b>"
    )

    if WEBAPP_URL and WEBAPP_URL.startswith("https://"):
        await message.answer(
            welcome_text,
            reply_markup=get_webapp_inline_keyboard(WEBAPP_URL)
        )
    else:
        await message.answer(welcome_text, reply_markup=get_main_menu(user_id))

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    """Jarayonni bekor qilish"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await message.answer("❌ Jarayon bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))

@router.message(F.text == "ℹ️ Qoidalar")
async def cmd_rules(message: Message):
    """Qoidalar"""
    await message.answer(DEFAULT_RULES)

@router.message(F.text == "📋 16 ta Ishtirokchi")
@router.message(F.text == "📋 Slotlar (1-16)")
async def cmd_slots_list(message: Message):
    """16 ta ishtirokchi va slotlar ro'yxati hamda yig'ilgan odam soni"""
    slots = await get_all_slots()
    tournament = await get_tournament()
    title = tournament.get("title", "Aurex PUBG Mobile Turniri")
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    
    text = format_slots_text(slots, title=title, stage_name=stage_name)
    await message.answer(text, reply_markup=get_slots_grid(slots))

@router.message(F.text == "🗓 O'yinlar jadvali")
async def cmd_schedule(message: Message):
    """O'yinlar jadvali (Chorak final, Yarim final, Final)"""
    matches = await get_all_matches()
    tournament = await get_tournament()
    start_date = tournament.get("start_date", "")
    
    text = format_schedule_text(matches, start_date=start_date)
    await message.answer(text)

@router.message(F.text == "👤 Mening slotim")
async def cmd_my_slot(message: Message):
    """Foydalanuvchining o'z sloti"""
    user_id = message.from_user.id
    user_slot = await get_user_slot(user_id)
    
    if not user_slot:
        slots = await get_all_slots()
        booked = sum(1 for s in slots if s.get("user_id"))
        await message.answer(
            f"⚠️ <b>Siz hali turnirga yozilmadingiz!</b>\n\n"
            f"📊 Hozirgi ishtirokchilar soni: <b>{booked}/16 ta</b>\n"
            f"O'z o'rningizni band qilish uchun <b>'🎮 Turnirga qatnashish'</b> tugmasini bosing!",
            reply_markup=get_main_menu(user_id)
        )
        return
        
    num = user_slot["slot_number"]
    nick = user_slot.get("pubg_nick") or "Noma'lum"
    pubg_id = user_slot.get("pubg_id") or "---"
    reg_time = user_slot.get("registered_at") or "---"
    
    tournament = await get_tournament()
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    room_id = tournament.get("room_id")
    room_pass = tournament.get("room_password")
    
    text = [
        f"🎯 <b>SIZNING TURNIR PROFILINGIZ:</b>\n",
        f"📍 <b>Slot raqami:</b> Slot #{num:02d}",
        f"👤 <b>PUBG Nickname:</b> <code>{nick}</code>",
        f"🆔 <b>PUBG ID:</b> <code>{pubg_id}</code>",
        f"⚔️ <b>Turnir bosqichi:</b> {stage_name}",
        f"🕒 <b>Ro'yxatdan o'tgan vaqt:</b> {reg_time}\n"
    ]
    
    if room_id and room_pass:
        text.append("🔥 <b>PUBG MOBILE XONASI OCHILGAN!</b>")
        text.append(f"🚪 <b>Room ID:</b> <code>{room_id}</code>")
        text.append(f"🔑 <b>Parol:</b> <code>{room_pass}</code>")
        text.append(f"⚠️ Diqqat: PUBG Mobile o'yinida aynan <b>Slot #{num:02d}</b> ga o'tiring!\n")
    else:
        text.append("⏳ <i>O'yin kuni PUBG Mobile xona ID va paroli botdan shaxsiy xabarda yuboriladi.</i>\n")
        
    await message.answer("\n".join(text), reply_markup=get_my_slot_actions(num))

@router.message(F.text == "🎮 Turnirga qatnashish")
async def cmd_participate(message: Message):
    """Turnirga qatnashish jarayoni"""
    user_id = message.from_user.id
    
    # Allaqachon slot olganmi?
    existing_slot = await get_user_slot(user_id)
    if existing_slot:
        await message.answer(
            f"⚠️ Siz allaqachon <b>Slot #{existing_slot['slot_number']:02d}</b> ni band qilgansiz!\n"
            f"👤 Nickname: <b>{existing_slot.get('pubg_nick')}</b>\n"
            f"🆔 PUBG ID: <code>{existing_slot.get('pubg_id')}</code>\n\n"
            f"Bitta o'yinchi faqat 1 ta o'rinda qatnashishi mumkin.",
            reply_markup=get_main_menu(user_id)
        )
        return

    tournament = await get_tournament()
    status = tournament.get("status", "registration")
    if status != "registration" and status != "open":
        await message.answer(
            "🚫 <b>Hozirda ro'yxatga olish yopiq!</b>\n"
            "Turnir o'yinlari boshlangan yoki yakunlangan. Keyingi turnirni kuting.",
            reply_markup=get_main_menu(user_id)
        )
        return

    slots = await get_all_slots()
    booked_count = sum(1 for s in slots if s.get("user_id"))
    
    if booked_count >= 16:
        await message.answer(
            "🚫 <b>Afsuski barcha 16 ta o'rin to'ldi!</b> (16/16)\n\n"
            "Chorak final o'yinlari tez kunda boshlanadi. Agar kimdir sloti bekor qilinsa, yana joy ochilishi mumkin.",
            reply_markup=get_main_menu(user_id)
        )
        return

    await message.answer(
        f"🎯 <b>AUREX PUBG MOBILE TURNIRIGA RO'YXATDAN O'TISH</b>\n\n"
        f"👥 Hozirda yig'ilgan odam: <b>{booked_count}/16 ta</b>\n"
        f"🟢 Bo'sh o'rinlar: <b>{16 - booked_count} ta</b>\n\n"
        f"O'zingizga ma'qul bo'lgan yashil slot raqamini bosing:",
        reply_markup=get_slots_grid(slots)
    )

@router.callback_query(F.data.startswith("select_slot:"))
async def callback_select_slot(callback: CallbackQuery, state: FSMContext):
    """Slot tanlanganda"""
    slot_num = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    existing_slot = await get_user_slot(user_id)
    if existing_slot:
        await callback.answer(
            f"Siz allaqachon Slot #{existing_slot['slot_number']} ni band qilgansiz!",
            show_alert=True
        )
        return
        
    slot = await get_slot(slot_num)
    if not slot or slot.get("user_id"):
        nick = slot.get("pubg_nick", "boshqa o'yinchi") if slot else ""
        await callback.answer(f"Slot #{slot_num} band ({nick})! Boshqa slotni tanlang.", show_alert=True)
        return
        
    await state.update_data(slot_number=slot_num)
    await state.set_state(RegistrationStates.waiting_for_pubg_nick)
    
    await callback.message.delete()
    await callback.message.answer(
        f"🎯 Siz <b>Slot #{slot_num:02d}</b> ni tanladingiz!\n\n"
        f"🎮 PUBG Mobile'dagi <b>Nickname</b>'ingizni yozib yuboring:",
        reply_markup=get_cancel_menu()
    )
    await callback.answer()

@router.message(RegistrationStates.waiting_for_pubg_nick)
async def process_pubg_nick(message: Message, state: FSMContext):
    """PUBG Nick qabul qilish"""
    nick = message.text.strip()
    if len(nick) < 2 or len(nick) > 30:
        await message.answer("⚠️ Nickname 2 dan 30 tagacha belgidan iborat bo'lishi kerak. Qaytadan yozing:")
        return
        
    await state.update_data(pubg_nick=nick)
    await state.set_state(RegistrationStates.waiting_for_pubg_id)
    
    await message.answer(
        f"✅ Nickname: <b>{nick}</b>\n\n"
        f"🆔 Endi <b>PUBG ID raqamingizni</b> kiriting (faqat raqamlar, masalan: <code>5123456789</code>):",
        reply_markup=get_cancel_menu()
    )

@router.message(RegistrationStates.waiting_for_pubg_id)
async def process_pubg_id(message: Message, state: FSMContext):
    """PUBG ID qabul qilish"""
    pubg_id = message.text.strip()
    if not pubg_id.isdigit() or len(pubg_id) < 5 or len(pubg_id) > 16:
        await message.answer("⚠️ PUBG ID faqat raqamlardan iborat bo'lishi kerak (masalan: <code>5123456789</code>). Qaytadan kiriting:")
        return
        
    await state.update_data(pubg_id=pubg_id)
    await state.set_state(RegistrationStates.waiting_for_phone)
    
    await message.answer(
        f"✅ PUBG ID: <code>{pubg_id}</code>\n\n"
        f"📱 Aloqa uchun telefon raqamingizni yuborasizmi? (Tugma orqali yoki o'tkazib yuborishingiz mumkin):",
        reply_markup=get_phone_menu()
    )

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Telefon raqam va ro'yxatni yakunlash"""
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    elif message.text and message.text != "⏭ O'tkazib yuborish":
        phone = message.text.strip()
        
    data = await state.get_data()
    slot_num = data.get("slot_number")
    pubg_nick = data.get("pubg_nick")
    pubg_id = data.get("pubg_id")
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username
    
    success = await book_slot(
        slot_number=slot_num,
        user_id=user_id,
        user_name=user_name,
        user_username=username,
        pubg_nick=pubg_nick,
        pubg_id=pubg_id,
        phone=phone
    )
    
    await state.clear()
    
    if success:
        slots = await get_all_slots()
        booked = sum(1 for s in slots if s.get("user_id"))

        congrats_text = (
            f"🎉 <b>TABRIKLAYMIZ! RO'YXATDAN O'TDINGIZ!</b>\n\n"
            f"📍 <b>Sizning slotingiz:</b> Slot #{slot_num:02d}\n"
            f"👤 <b>PUBG Nick:</b> <code>{pubg_nick}</code>\n"
            f"🆔 <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
            f"📊 <b>Hozirgi ishtirokchilar:</b> {booked}/16 ta\n\n"
            f"ℹ️ <b>Eslatma:</b>\n"
            f"• Turnir PUBG Mobile ilovasida maxsus xonada (Custom Room) bo'lib o'tadi.\n"
            f"• O'yinlar har 2 kunda 2 ta o'yindan iborat bo'ladi.\n"
            f"• Xona ID va Parol o'yin kuni bot orqali sizga yuboriladi!\n\n"
            f"Jangga tayyormisiz? Omad tilaymiz! 🏆"
        )
        await message.answer(congrats_text, reply_markup=get_main_menu(user_id))
    else:
        await message.answer(
            f"⚠️ Afsuski, siz tanlagan Slot #{slot_num} boshqa o'yinchi tomonidan band qilindi. "
            f"Iltimos, qaytadan boshqa bo'sh o'rinni tanlang.",
            reply_markup=get_main_menu(user_id)
        )

@router.callback_query(F.data.startswith("cancel_slot:"))
async def callback_cancel_slot(callback: CallbackQuery):
    """Slotni bekor qilish"""
    slot_num = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    success = await cancel_slot(slot_number=slot_num, user_id=user_id)
    if success:
        await callback.message.edit_text(
            f"✅ <b>Slot #{slot_num:02d} bekor qilindi va bo'shatildi.</b>\n"
            f"Istalgan vaqtda qaytadan yangi slot tanlashingiz mumkin."
        )
        await callback.answer("Slotingiz bekor qilindi!")
    else:
        await callback.answer("Xatolik yoki bu slot sizga tegishli emas!", show_alert=True)

@router.callback_query(F.data == "refresh_slots")
async def callback_refresh_slots(callback: CallbackQuery):
    """Slotlar ro'yxatini yangilash"""
    slots = await get_all_slots()
    tournament = await get_tournament()
    title = tournament.get("title", "Aurex PUBG Mobile Turniri")
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    
    text = format_slots_text(slots, title=title, stage_name=stage_name)
    try:
        await callback.message.edit_text(text, reply_markup=get_slots_grid(slots))
        await callback.answer("Ro'yxat yangilandi 🔄")
    except Exception:
        await callback.answer("O'zgarish yo'q")

@router.callback_query(F.data == "refresh_my_slot")
async def callback_refresh_my_slot(callback: CallbackQuery):
    """Mening slotim oynasini yangilash"""
    user_id = callback.from_user.id
    user_slot = await get_user_slot(user_id)
    
    if not user_slot:
        await callback.message.edit_text("Sizda band qilingan slot yo'q.")
        await callback.answer()
        return
        
    num = user_slot["slot_number"]
    nick = user_slot.get("pubg_nick") or "Noma'lum"
    pubg_id = user_slot.get("pubg_id") or "---"
    reg_time = user_slot.get("registered_at") or "---"
    
    tournament = await get_tournament()
    stage_name = tournament.get("stage_name", "Ro'yxatga olish")
    room_id = tournament.get("room_id")
    room_pass = tournament.get("room_password")
    
    text = [
        f"🎯 <b>SIZNING TURNIR PROFILINGIZ:</b>\n",
        f"📍 <b>Slot raqami:</b> Slot #{num:02d}",
        f"👤 <b>PUBG Nickname:</b> <code>{nick}</code>",
        f"🆔 <b>PUBG ID:</b> <code>{pubg_id}</code>",
        f"⚔️ <b>Turnir bosqichi:</b> {stage_name}",
        f"🕒 <b>Ro'yxatdan o'tgan vaqt:</b> {reg_time}\n"
    ]
    
    if room_id and room_pass:
        text.append("🔥 <b>PUBG MOBILE XONASI OCHILGAN!</b>")
        text.append(f"🚪 <b>Room ID:</b> <code>{room_id}</code>")
        text.append(f"🔑 <b>Parol:</b> <code>{room_pass}</code>")
        text.append(f"⚠️ Diqqat: PUBG Mobile o'yinida aynan <b>Slot #{num:02d}</b> ga o'tiring!\n")
    else:
        text.append("⏳ <i>O'yin kuni PUBG Mobile xona ID va paroli botdan shaxsiy xabarda yuboriladi.</i>\n")
        
    try:
        await callback.message.edit_text("\n".join(text), reply_markup=get_my_slot_actions(num))
        await callback.answer("Ma'lumotlar yangilandi 🔄")
    except Exception:
        await callback.answer("O'zgarish yo'q")
