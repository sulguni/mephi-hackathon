import aiosqlite
from collections import namedtuple

DATABASE_NAME = "db.db"

class User(namedtuple("User", ["name", "group", "gavrilova", "fmba", "last_gavrilova", "last_fmba", "contacts", "phone", "stranger"])):
    pass

async def find_user_by_phone(phone: str):
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute("SELECT Name, GroupID, Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Phone, Stranger from Donors where Phone = ?", (phone,))
        row = await cur.fetchone()
        if row is None:
            return None
        return User._make(row)

async def find_user_by_names(name: str):
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute("SELECT Name, GroupID, Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Phone, Stranger from Donors where Name = ?", (name,))
        row = await cur.fetchone()
        if row is None:
            return None
        return User._make(row)

async def find_user_by_id(donorID: int):
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute("SELECT Name, GroupID, Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Phone, Stranger from Donors where donorID = ?", (donorID,))
        row = await cur.fetchone()
        if row is None:
            return None
        return User._make(row)

async def execute(query: str, params, fetch=False):
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute(query, params)
        await con.commit()
        if fetch:
            return await(cur.fetchone()) is not None
        return True

async def get_user_state(id: int):
    async with aiosqlite.connect(DATABASE_NAME) as con, con.cursor() as cur:
        cur = await cur.execute("select state from UserStates where UserID = ?", (id,))
        m = await cur.fetchone()
        return 0 if not m else m[0]
