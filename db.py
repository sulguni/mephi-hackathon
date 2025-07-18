import aiosqlite
from collections import namedtuple

DATABASE_NAME = "db.db"

class User(namedtuple("User", ["surname", "name", "patronim", "group", "gavrilova", "fmba", "last_gavrilova", "last_fmba", "contacts", "phone", "stranger"])):
    pass

async def seen_user(id: int):
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        return await cur.execute("SELECT UserID from BotUsers where UserID = ?", (id,)) != None

async def mark_seen(id: int):
    if await seen_user(id):
        return
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        await cur.execute("INSERT INTO BotUsers (UserID) values (?)", (id,))

async def find_user_by_phone(phone: str) -> User | None:
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute("SELECT Surname, Name, Patronim, GroupID, Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Phone, Stranger from Donors where Phone = ?", (phone,))
        row = await cur.fetchone()
        if row == None:
            return None
        return User._make(row)

async def find_user_by_names(name: str, surname: str, patronim: str) -> User | None:
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute("SELECT Surname, Name, Patronim, GroupID, Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Phone, Stranger from Donors where Name = ? AND Surname = ? AND Patronim = ?", (name, surname, patronim))
        row = await cur.fetchone()
        if row == None:
            return None
        return User._make(row)
