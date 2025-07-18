import asyncio
import logging
import re
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
import states

import db

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")


# All handlers should be attached to the Router (or Dispatcher)

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
    t = message.text or ""
    if re.match(r"\+\d+", t):
        pass # чёто с ним делаем
    else:
        await message.answer("Введите корректный номер телефона (начинается с плюса и последовательности цифр)")

@dp.message(Command('admin'), states.IsAdmin())
async def admin_command(message: Message) -> None:

    admin_kb= [
        [InlineKeyboardButton(text="Редактировать данные доноров", callback_data='donor_edit')],
        [InlineKeyboardButton(text="Изменить информацию в боте", callback_data='bot_edit')],
        [InlineKeyboardButton(text="Просмотреть статистику", callback_data='view_statistics')],
        [InlineKeyboardButton(text="Ответить на вопросы", callback_data='reply_to_questions')],
        [InlineKeyboardButton(text="Сделать рассылку", callback_data='newsletter'),
         InlineKeyboardButton(text="Создать мероприятие", callback_data='create_event')],
        [InlineKeyboardButton(text="Загрузить статистику", callback_data='upload_statistics'),
         InlineKeyboardButton(text="Получить статистику", callback_data='get_statistics')],
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=admin_kb)

    await message.answer('Добро пожаловать в панель организатора!\n'
                         'Выберите желаемое действие:', reply_markup=keyboard)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
