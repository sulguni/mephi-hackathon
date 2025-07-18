from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

class UserState(StatesGroup):
    phone = State()
    edit_name = State()


admin_ids = [5235789211]


class IsAdmin(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return obj.from_user.id in admin_ids
