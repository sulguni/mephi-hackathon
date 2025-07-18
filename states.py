from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import BaseFilter

class UserState(StatesGroup):
    phone = State()

admin_ids = [5630011467]


class IsAdmin(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return obj.from_user.id in admin_ids