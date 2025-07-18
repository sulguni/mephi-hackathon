import asyncio
import logging
import re
import sys
from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
import states
from handlers import admin_handlers, menu
import db
from dotenv import load_dotenv

load_dotenv()
# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")
INLINE_BTN = lambda text, data: InlineKeyboardButton(text=text, callback_data=data)
INLINE_KEYBOARD = lambda buttons: InlineKeyboardMarkup(inline_keyboard=buttons)



dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    if await db.seen_user(message.from_user.id):
        await message.reply("С возращением!")
    else:
        await db.mark_seen(message.from_user.id)

        await message.answer('Привет, я бот для помощи участникам и организаторам донорских дней в МИФИ. Для начала тебе нужно зарегестрироваться.\n'
                         ' Пожалуйста, введи свой номер телефона')
        await state.set_state(states.UserState.phone)

@dp.message(states.UserState.phone)
async def phone_number_msg(message: Message):
    t = (message.text or "").strip()
    if re.match(r"\+\d+", t):
        user = await db.find_user_by_phone(t)
        if user != None:
            await handle_seen_user(message, user)
        else:
            await try_finding_user_by_name(message)
    else:
        await message.answer("Введите корректный номер телефона (начинается с плюса и последовательности цифр)")

async def handle_seen_user(message: Message, user: db.User):
    await message.answer(f"Нашли пользователя с таким номером. Вы {user.name}?", reply_markup=INLINE_KEYBOARD([
        [INLINE_BTN("Да", "confirm_name"), INLINE_BTN("Нет, редактировать ФИО", "edit_name")]
    ]))

@dp.callback_query(F.data == "confirm_name", F.message)
async def handle_confirm_name(query: CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=None)
    await send_agreement(query)

@dp.callback_query(F.data == "edit_name", F.message)
async def handle_edit_name(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text(text="Введите ваше ФИО")
    await state.set_state(states.UserState.edit_name)



async def send_agreement(chat: CallbackQuery):
    chat.answer("Примите соглашение")

async def try_finding_user_by_name(message: Message):

    pass



async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(admin_handlers.router)
    dp.include_router(menu.router)
    # And the run events dispatching
    await dp.start_polling(bot)




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
