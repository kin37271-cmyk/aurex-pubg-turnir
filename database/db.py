import aiosqlite
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tournament.db")

async def init_db():
    """Baza jadvallarini yaratish va yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Turnir holati jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tournament (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT 'Aurex PUBG Turniri',
                status TEXT DEFAULT 'registration', -- registration, chorak_final, yarim_final, final, finished
                stage_name TEXT DEFAULT 'Ro''yxatga olish',
                start_date TEXT DEFAULT NULL,
                slot_price INTEGER DEFAULT 0, -- 0 = bepul / tekin, yoki summa (masalan: 20000)
                room_id TEXT DEFAULT NULL,
                room_password TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: slot_price ustuni mavjud bo'lmasa qo'shish
        try:
            await db.execute("ALTER TABLE tournament ADD COLUMN slot_price INTEGER DEFAULT 0")
        except Exception:
            pass
        
        # 16 ta Slot jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                slot_number INTEGER PRIMARY KEY,
                user_id INTEGER DEFAULT NULL,
                user_name TEXT DEFAULT NULL,
                user_username TEXT DEFAULT NULL,
                pubg_nick TEXT DEFAULT NULL,
                pubg_id TEXT DEFAULT NULL,
                phone TEXT DEFAULT NULL,
                status TEXT DEFAULT 'active', -- active, eliminated, winner
                registered_at TIMESTAMP DEFAULT NULL
            )
        """)

        # O'yinlar jadvali (Har 2 kunda 2 ta o'yin)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage TEXT, -- Chorak final, Yarim final, Final
                day_offset INTEGER, -- 0, 2, 4, 6 (har 2 kunda)
                game_index INTEGER, -- 1-o'yin, 2-o'yin
                match_date TEXT,
                match_time TEXT,
                status TEXT DEFAULT 'pending' -- pending, active, completed
            )
        """)

        # Barcha foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                pubg_nick TEXT,
                pubg_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()

        # Dastlabki turnir mavjudligini tekshirish
        async with db.execute("SELECT COUNT(*) FROM tournament") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                await db.execute("""
                    INSERT INTO tournament (title, status, stage_name) 
                    VALUES ('Aurex PUBG Mobile Turniri #1', 'registration', 'Ro''yxatga olish')
                """)
                await db.commit()

        # 16 ta slotni yaratish
        async with db.execute("SELECT COUNT(*) FROM slots") as cursor:
            slot_count = (await cursor.fetchone())[0]
            if slot_count < 16:
                for i in range(1, 17):
                    await db.execute(
                        "INSERT OR IGNORE INTO slots (slot_number) VALUES (?)",
                        (i,)
                    )
                await db.commit()

async def get_tournament() -> Dict[str, Any]:
    """Faol turnir ma'lumotlarini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tournament ORDER BY id DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}

async def update_tournament_stage(status: str, stage_name: str, start_date: Optional[str] = None):
    """Turnir bosqichini yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        if start_date:
            await db.execute("""
                UPDATE tournament 
                SET status = ?, stage_name = ?, start_date = ? 
                WHERE id = (SELECT MAX(id) FROM tournament)
            """, (status, stage_name, start_date))
        else:
            await db.execute("""
                UPDATE tournament 
                SET status = ?, stage_name = ? 
                WHERE id = (SELECT MAX(id) FROM tournament)
            """, (status, stage_name))
        await db.commit()

async def set_room_details(room_id: str, room_password: str):
    """Xona ID va parolini saqlash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE tournament 
            SET room_id = ?, room_password = ? 
            WHERE id = (SELECT MAX(id) FROM tournament)
        """, (room_id, room_password))
        await db.commit()

async def update_slot_price(price: int):
    """Slot narxini yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE tournament 
            SET slot_price = ? 
            WHERE id = (SELECT MAX(id) FROM tournament)
        """, (price,))
        await db.commit()

async def reset_tournament(new_title: Optional[str] = None):
    """Yangi turnir boshlash - barcha 16 ta slot va o'yinlarni tozalash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE slots SET 
                user_id = NULL,
                user_name = NULL,
                user_username = NULL,
                pubg_nick = NULL,
                pubg_id = NULL,
                phone = NULL,
                status = 'active',
                registered_at = NULL
        """)
        await db.execute("DELETE FROM matches")
        title = new_title or "Aurex PUBG Mobile Turniri"
        await db.execute("""
            INSERT INTO tournament (title, status, stage_name) 
            VALUES (?, 'registration', 'Ro''yxatga olish')
        """, (title,))
        await db.commit()

async def get_all_slots() -> List[Dict[str, Any]]:
    """Barcha 16 ta slot ma'lumotlarini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM slots ORDER BY slot_number ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_slot(slot_number: int) -> Optional[Dict[str, Any]]:
    """Aynan bitta slot ma'lumotlarini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM slots WHERE slot_number = ?", (slot_number,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_user_slot(user_id: int) -> Optional[Dict[str, Any]]:
    """Foydalanuvchi band qilgan slotni topish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM slots WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def book_slot(
    slot_number: int,
    user_id: int,
    user_name: str,
    user_username: Optional[str],
    pubg_nick: str,
    pubg_id: str,
    phone: Optional[str] = None
) -> bool:
    """Slotni band qilish"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Avval slot bo'shmi yoki yo'qligini tekshiramiz
        async with db.execute("SELECT user_id FROM slots WHERE slot_number = ?", (slot_number,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] is not None:
                return False
        
        # Foydalanuvchi oldin boshqa slot olmaganligini tekshiramiz (user_id mavjud bo'lsa)
        if user_id and user_id > 0:
            async with db.execute("SELECT slot_number FROM slots WHERE user_id = ?", (user_id,)) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    return False


        await db.execute("""
            UPDATE slots SET 
                user_id = ?,
                user_name = ?,
                user_username = ?,
                pubg_nick = ?,
                pubg_id = ?,
                phone = ?,
                status = 'active',
                registered_at = CURRENT_TIMESTAMP
            WHERE slot_number = ?
        """, (user_id, user_name, user_username, pubg_nick, pubg_id, phone, slot_number))

        await db.execute("""
            INSERT INTO users (user_id, full_name, username, pubg_nick, pubg_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username,
                pubg_nick = excluded.pubg_nick,
                pubg_id = excluded.pubg_id
        """, (user_id, user_name, user_username, pubg_nick, pubg_id))

        await db.commit()
        return True

async def cancel_slot(slot_number: int, user_id: Optional[int] = None) -> bool:
    """Slotni bo'shatish"""
    async with aiosqlite.connect(DB_PATH) as db:
        if user_id:
            res = await db.execute("""
                UPDATE slots SET 
                    user_id = NULL,
                    user_name = NULL,
                    user_username = NULL,
                    pubg_nick = NULL,
                    pubg_id = NULL,
                    phone = NULL,
                    status = 'active',
                    registered_at = NULL
                WHERE slot_number = ? AND user_id = ?
            """, (slot_number, user_id))
        else:
            res = await db.execute("""
                UPDATE slots SET 
                    user_id = NULL,
                    user_name = NULL,
                    user_username = NULL,
                    pubg_nick = NULL,
                    pubg_id = NULL,
                    phone = NULL,
                    status = 'active',
                    registered_at = NULL
                WHERE slot_number = ?
            """, (slot_number,))
        await db.commit()
        return res.rowcount > 0

async def get_registered_players() -> List[Dict[str, Any]]:
    """Ro'yxatdan o'tgan barcha 16 ta o'yinchilar"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM slots WHERE user_id IS NOT NULL ORDER BY slot_number ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def create_schedule(start_date: datetime) -> List[Dict[str, Any]]:
    """
    O'yinlar jadvalini yaratish:
    Har 2 kunda 2 ta o'yin bo'ladi!
    - 1-kun (Chorak final 1-qism): 1-o'yin (20:00), 2-o'yin (21:00)
    - 3-kun (Chorak final 2-qism): 1-o'yin (20:00), 2-o'yin (21:00)
    - 5-kun (Yarim final): 1-o'yin (20:00), 2-o'yin (21:00)
    - 7-kun (GRAND FINAL): 1-o'yin (20:00), 2-o'yin (21:00)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM matches")
        
        stages_plan = [
            ("Chorak final (1-kun)", 0),
            ("Chorak final (2-kun)", 2),
            ("Yarim final", 4),
            ("🏆 GRAND FINAL", 6)
        ]
        
        created = []
        for stage_name, day_offset in stages_plan:
            match_date = start_date + timedelta(days=day_offset)
            date_str = match_date.strftime("%d-%m-%Y")
            
            # Har bir o'yin kunida 2 ta o'yin
            for game_idx, match_time in [(1, "20:00"), (2, "21:00")]:
                cursor = await db.execute("""
                    INSERT INTO matches (stage, day_offset, game_index, match_date, match_time, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (stage_name, day_offset, game_idx, date_str, match_time))
                created.append({
                    "id": cursor.lastrowid,
                    "stage": stage_name,
                    "date": date_str,
                    "time": match_time,
                    "game_index": game_idx
                })
                
        await db.commit()
        return created

async def get_all_matches() -> List[Dict[str, Any]]:
    """Barcha o'yinlar ro'yxatini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM matches ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_stats() -> Dict[str, Any]:
    """Statistika"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM slots WHERE user_id IS NOT NULL") as c1:
            booked_slots = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users") as c2:
            total_users = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM matches") as c3:
            total_matches = (await c3.fetchone())[0]
        return {
            "booked_slots": booked_slots,
            "total_slots": 16,
            "total_users": total_users,
            "total_matches": total_matches
        }
