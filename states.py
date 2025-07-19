from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

import db

class UserState(StatesGroup):
    phone = State()
    edit_name = State()
    group = State()


class EditDonor(StatesGroup):
    waiting_phone = State()
    waiting_field = State()
    waiting_value = State()

class AddDonorsState(StatesGroup):
    waiting_for_text = State()

class EventState(StatesGroup):
    waiting_for_event = State()

class DocumentState(StatesGroup):
    waiting_for_document = State()

class NewsletterStates(StatesGroup):
    waiting_for_message = State()

admin_ids = [5235789211, 1194604421]


class IsAdmin(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return await db.get_user_state(obj.from_user.id) == 2

class Accepted(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return await db.get_user_state(obj.from_user.id) == 1

class NotAccepted(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return await db.get_user_state(obj.from_user.id) == 0
