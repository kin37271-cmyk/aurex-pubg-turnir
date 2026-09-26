from typing import List, Dict, Any

def format_slots_text(slots: List[Dict[str, Any]], title: str = "Aurex PUBG Turniri", stage_name: str = "Ro'yxatga olish") -> str:
    """Foydalanuvchilar va bot uchun 16 ta slot holati"""
    booked_count = sum(1 for s in slots if s.get("user_id"))
    
    text = [
        f"🏆 <b>{title}</b>",
        f"📍 <b>Hozirgi Bosqich:</b> {stage_name}",
        f"👥 <b>Format:</b> 16 ta PUBG Mobile o'yinchisi (Solo)",
        f"📊 <b>Yig'ilgan odam:</b> {booked_count}/16 ta\n",
        "📋 <b>16 TA ISHTIROKCHI RO'YXATI:</b>"
    ]
    
    for s in slots:
        num = s["slot_number"]
        if s.get("user_id"):
            nick = s.get("pubg_nick") or "Ishtirokchi"
            pubg_id = s.get("pubg_id") or "---"
            text.append(f"<b>[Slot #{num:02d}]</b> 🔴 <b>{nick}</b> (ID: <code>{pubg_id}</code>)")
        else:
            text.append(f"<b>[Slot #{num:02d}]</b> 🟢 <i>Bo'sh o'rin</i>")
            
    if booked_count == 16:
        text.append("\n🔥 <b>16 ta odam to'liq yig'ildi! Turnir boshlanishga tayyor.</b>")
    else:
        text.append(f"\n⚡️ <i>Yana {16 - booked_count} ta bo'sh joy qoldi!</i>")
        
    return "\n".join(text)

def format_schedule_text(matches: List[Dict[str, Any]], start_date: str = "") -> str:
    """O'yinlar jadvalini ko'rsatish (Har 2 kunda 2 ta o'yin)"""
    if not matches:
        return (
            "📅 <b>TURNIR O'YINLAR JADVALI:</b>\n\n"
            "⚠️ O'yinlar jadvali hali admin tomonidan e'lon qilinmadi.\n\n"
            "ℹ️ <b>Tartib:</b>\n"
            "• Turnir PUBG Mobile maxsus xonasida (Custom Room) bo'ladi.\n"
            "• O'yinlar har 2 kunda 2 tadan o'tkaziladi:\n"
            "   1️⃣ Chorak final (1-kun) — 2 ta o'yin\n"
            "   2️⃣ Chorak final (2-kun) — 2 ta o'yin\n"
            "   3️⃣ Yarim final — 2 ta o'yin\n"
            "   🏆 GRAND FINAL — 2 ta o'yin"
        )

    lines = [
        "🗓 <b>AUREX PUBG TURNIR O'YINLAR JADVALI</b> ⚔️",
        "🎮 <i>O'yinlar PUBG Mobile Custom Room'da bo'ladi!</i>",
        "⏱ <b>Qoida:</b> Har 2 kunda 2 ta o'yin o'tkaziladi!\n"
    ]

    current_stage = None
    for m in matches:
        stage = m.get("stage", "Bosqich")
        date_str = m.get("match_date", "---")
        time_str = m.get("match_time", "---")
        game_idx = m.get("game_index", 1)

        if stage != current_stage:
            current_stage = stage
            lines.append(f"\n⚔️ <b>{stage}</b> (Sana: {date_str}):")

        lines.append(f"   ├ 🎮 <b>{game_idx}-o'yin:</b> Soat {time_str}")

    lines.append("\n⚠️ <i>Xona ID va Parol o'yin boshlanishidan 10 daqiqa oldin faqat 16 ishtirokchiga bot orqali yuboriladi!</i>")
    return "\n".join(lines)

def format_channel_post(
    slots: List[Dict[str, Any]],
    title: str = "Aurex PUBG Mobile Turniri",
    bot_username: str = "",
    stage_name: str = "Ro'yxatga olish",
    start_date: str = ""
) -> str:
    """Telegram kanalga e'lon berish uchun format"""
    booked_count = sum(1 for s in slots if s.get("user_id"))

    lines = [
        "🔥 <b>AUREX PUBG MOBILE TOURNAMENT</b> 🔥",
        f"🏆 <b>Turnir:</b> {title}",
        f"📍 <b>Bosqich:</b> {stage_name}",
        f"👥 <b>Format:</b> Solo (16 ta ishtirokchi)",
        f"⏱ <b>Tizim:</b> Har 2 kunda 2 ta o'yin (Custom Room)",
        f"📊 <b>Yig'ilgan o'yinchilar:</b> {booked_count}/16 ta\n"
    ]

    if start_date:
        lines.append(f"📅 <b>Boshlanish sanasi:</b> {start_date}\n")

    lines.append("📋 <b>Slotlar va Qatnashuvchilar:</b>")
    for s in slots:
        num = s["slot_number"]
        if s.get("user_id"):
            nick = s.get("pubg_nick") or "Ishtirokchi"
            lines.append(f"├ <b>Slot #{num:02d}</b>: 🔴 {nick}")
        else:
            lines.append(f"├ <b>Slot #{num:02d}</b>: 🟢 <i>Bo'sh</i>")

    lines.append("\n" + "—" * 22)
    if booked_count == 16:
        lines.append("🚨 <b>16 ta odam to'liq yig'ildi!</b>")
        lines.append("Tez orada Chorak final o'yinlari start oladi!")
    else:
        lines.append("⚡️ <b>O'z slotingizni band qiling! Joylar chegaralangan (16 ta):</b>")
        if bot_username:
            lines.append(f"👉 <b>Ro'yxatdan o'tish boti:</b> @{bot_username}")

    return "\n".join(lines)

def get_final_fireworks_text(title: str = "Aurex PUBG Turniri", winner_info: str = "") -> str:
    """Final va salyut animatsiyasi uchun maxsus tantanali matn (Yagona 1-o'rin, killsiz)"""
    return (
        "🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇\n"
        "✨✨✨ <b>GRAND FINAL VA SALYUT!</b> ✨✨✨\n"
        "🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇\n\n"
        f"🏆 <b>{title} - GRAND FINAL!</b> 🏆\n\n"
        "🔥 <b>16 nafar ishtirokchi o'rtasidagi shiddatli jang yakunlandi!</b> 🔥\n\n"
        f"{winner_info}\n\n"
        "🎉 <b>Yagona Chempionni chin dildan tabriklaymiz!</b> 🎉\n"
        "🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇🎆🎇"
    )
