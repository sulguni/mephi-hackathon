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
    user = await db.find_user_by_id(message.from_user.id)
    if user:
        t = "С возращением!"
        if user.phone == "":
            t += " Регистрация не завершена, для завершения введите номер телефона"
            await state.set_state(states.UserState.phone)
        elif user.name == "":
            t += " Регистрация не завершена, для завершения введите ФИО"
            await state.set_state(states.UserState.edit_name)
        await message.reply(t)
        await state.update_data(new=False)
    else:
        await message.answer('Привет, я бот для помощи участникам и организаторам донорских дней в МИФИ. Для начала тебе нужно зарегестрироваться.\n'
                         'Пожалуйста, введи свой номер телефона')
        await state.set_state(states.UserState.phone)
        await state.update_data(new=True)

@dp.message(states.UserState.phone)
async def phone_number_msg(message: Message, state: FSMContext):
    t = (message.text or "").strip()
    if re.match(r"\+\d+", t):
        user = await db.find_user_by_phone(t)
        await state.update_data(phone=t)
        if user:
            await state.update_data(name=user.name)
            await message.answer(f"Нашли пользователя с таким номером. Вы {user.name}?", reply_markup=INLINE_KEYBOARD([
                [INLINE_BTN("Да", "confirm_name"), INLINE_BTN("Нет, редактировать ФИО", "edit_name")]
            ]))
        else:
            await message.answer("Пожалуйста, введите ваше ФИО")
            await state.set_state(states.UserState.edit_name)
    else:
        await message.answer("Введите корректный номер телефона (плюс и далее последовательности цифр)")


@dp.callback_query(F.data == "confirm_name", F.message)
async def handle_confirm_name(query: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    if await db.execute("select Name from Donors where Name = ? AND IFNULL(Phone, '') = ''", (d["name"],), True):
        await db.execute("UPDATE Donors set Phone = ?, donorID = ? where Name = ? AND IFNULL(Phone, '') = ''",
                         (d["phone"], query.from_user.id, d["name"]))
    elif await db.execute("select Phone from Donors where Phone = ?", (d["phone"],), True):
        await db.execute("UPDATE Donors set Name = ?, donorID = ? where Phone = ?", (d["name"], query.from_user.id, d["phone"]))
    else:
        await db.execute("INSERT INTO Donors (Name, donorID, Phone) values (?, ?, ?)",
                         (d["name"], query.from_user.id, d["phone"]))
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.edit_text("ФИО сохранено.")
    await state.clear()
    await send_agreement(query)

@dp.callback_query(F.data == "edit_name", F.message)
async def handle_edit_name(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text(text="Пожалуйста, введите ваше ФИО")
    await state.set_state(states.UserState.edit_name)

@dp.message(states.UserState.edit_name)
async def handle_name_msg(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Отправьте текст")
        return
    t = message.text
    await state.update_data(name=t)
    await message.answer(f"Ваше ФИО: {t}, верно?", reply_markup=INLINE_KEYBOARD([
        [INLINE_BTN("Да", "confirm_name"), INLINE_BTN("Нет, редактировать ФИО", "edit_name")]
    ]))

async def send_agreement(chat: CallbackQuery):
    await chat.answer("Примите соглашение")

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
