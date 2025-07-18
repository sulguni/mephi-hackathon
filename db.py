import aiosqlite

async def seen_user(id: int):
    async with aiosqlite.connect("db.db") as con, con.cursor() as cur:
        return await cur.execute("SELECT UserID from BotUsers where UserID = ?", (id,)) != None

async def mark_seen(id: int):
    if await seen_user(id):
        return
    async with aiosqlite.connect("db.db") as con, con.cursor() as cur:
        await cur.execute("INSERT INTO BotUsers (UserID) values (?)", (id,))
