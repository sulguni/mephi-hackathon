from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject



class UserState(StatesGroup):
    phone = State()
    edit_name = State()


class EditDonor(StatesGroup):
    waiting_phone = State()
    waiting_field = State()
    waiting_value = State()

class AddDonorsState(StatesGroup):
    waiting_for_text = State()

class EventState(StatesGroup):
    waiting_for_event = State()

admin_ids = [5235789211, 1194604421]


class IsAdmin(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return obj.from_user.id in admin_ids
