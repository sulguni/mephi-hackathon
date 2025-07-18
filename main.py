import asyncio
import logging
from re import L
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
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
async def admin_newsletter_step_2(message: Message):
    print(message.text)

@dp.message(Command('admin'), states.IsAdmin())
async def admin_command(message: Message) -> None:
    await message.answer('Добро пожаловать в панель организатора!')

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
