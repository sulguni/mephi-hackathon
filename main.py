import asyncio
import logging
import re
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
import states

import db

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

INLINE_BTN = lambda text, data: InlineKeyboardButton(text=text, callback_data=data)
INLINE_KEYBOARD = lambda buttons: InlineKeyboardMarkup(inline_keyboard=buttons)

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


@dp.message(Command('admin'), states.IsAdmin())
async def admin_command(message: Message) -> None:
    await message.answer('Добро пожаловать в панель организатора!\n'
                         'Выберите желаемое действие:', reply_markup=keyboard)

@dp.callback_query(F.data == "admin_menu")
async def back_to_admin(callback: CallbackQuery):
    await callback.message.edit_text('Добро пожаловать в панель организатора!\n'
                         'Выберите желаемое действие:', reply_markup=keyboard)

kb_return = [
    [InlineKeyboardButton(text="Вернуться", callback_data='admin_menu')]]
keyboard_return = InlineKeyboardMarkup(inline_keyboard=kb_return)

@dp.callback_query(F.data == "donor_edit")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Отправьте данные которые желаете изменить/добавить",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "bot_edit")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Выберите, что хотите изменить",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "view_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Статистика:",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "reply_to_questions")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Вопрос:",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "newsletter")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Выберите категорию для рассылки",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "create_event")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Для создания мероприятия введите дату и "
                                     "центр крови",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "upload_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Для загрузки статистики отправьте файл в формате exel",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == "get_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Вот ваш документ",
                                     reply_markup=keyboard_return)

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
