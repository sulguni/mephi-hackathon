import asyncio
import logging
import re
import sys
from os import getenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
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

@dp.message(Command("accept"))
async def accept(message: Message, state: FSMContext):
    await db.execute("insert into UserStates (UserID, state) values (?, ?)", (message.from_user.id, 1))
    await command_start_handler(message, state)

@dp.message(states.NotAccepted())
async def not_accepted(message: Message):
    await message.answer("Перед работой с ботом необходимо согласиться с <a href='https://drive.google.com/file/d/1lbAdchMWSQy-tnM-1NCd4qjYOHlMop6F/view?usp=sharing'>политикой обработки персональных данных</a>\n Для этого выполните: /accept")

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user = await db.find_user_by_id(message.from_user.id)
    if user:
        t = "С возращением!"
        phone = False
        if user.phone == "":
            t += " Регистрация не завершена, для завершения введите номер телефона"
            await state.set_state(states.UserState.phone)
            phone = True
        elif user.name == "":
            t += " Регистрация не завершена, для завершения введите ФИО"
            await state.set_state(states.UserState.edit_name)
        await message.reply(t, reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]]) if phone else None)
        await state.update_data(new=False)
    else:
        await message.answer('Привет, я бот для помощи участникам и организаторам донорских дней в МИФИ. Для начала тебе нужно зарегестрироваться.\n'
                         'Пожалуйста, введи свой номер телефона', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]]))
        await state.set_state(states.UserState.phone)
        await state.update_data(new=True)


@dp.message(states.UserState.phone)
async def phone_number_msg(message: Message, state: FSMContext):
    t = ""
    if message.contact is not None:
        t = message.contact.phone_number
    elif message.text is not None:
        t = message.text
    if re.match(r"\+?[\d\-()]+", t):
        user = await db.find_user_by_phone(t)
        await state.update_data(phone=t)
        if user:
            await state.update_data(name=user.name)
            await message.answer(f"Нашли пользователя с таким номером. Вы {user.name}?", reply_markup=INLINE_KEYBOARD([
                [INLINE_BTN("Да", "confirm_name"), INLINE_BTN("Нет, редактировать ФИО", "edit_name")]
            ]))
        else:
            await message.answer("Пожалуйста, введите ваше ФИО", reply_markup=None)
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
    await query.answer()
    if await db.execute("select donorID from Donors where donorID = ? AND IFNULL(GroupID, '') = ''", (query.from_user.id,), True):
        await query.message.answer("Кем вы являетесь?", reply_markup=INLINE_KEYBOARD(
            [
                [INLINE_BTN("Студент МИФИ", "student_role")],
                [INLINE_BTN("Сотрудник МИФИ", "staff_role")],
                [INLINE_BTN("Я не из МИФИ", "other_role")]
            ]
        ))
    else:
        await query.message.answer("Вы зарегистировались!", reply_markup=INLINE_KEYBOARD([[INLINE_BTN("В меню", "menu")]]))

@dp.callback_query(F.data.endswith("_role"), F.message)
async def handle_role(query: CallbackQuery, state: FSMContext):
    await query.answer()
    role = query.data.split('_')[0]
    if role == "student":
        await state.set_state(states.UserState.group)
        await query.message.answer("Укажите вашу группу")
    else:
        await db.execute(f"update Donors set GroupID={'\"Сотрудник\"' if role == 'staff' else '\"\"'} where donorID = ?", (query.from_user.id,))
        await query.message.answer("Вы зарегистировались!",
                                   reply_markup=INLINE_KEYBOARD([[INLINE_BTN("В меню", "menu")]]))

@dp.message(states.UserState.group, F.text)
async def handle_group(message: Message, state: FSMContext):
    await db.execute(f"update Donors set GroupID=? where donorID = ?",
                     (message.text, message.from_user.id,))
    await message.answer("Вы зарегистировались!", reply_markup=INLINE_KEYBOARD([[INLINE_BTN("В меню", "menu")]]))
    await state.clear()

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

async def send_agreement(query: CallbackQuery):
    await query.answer("Примите соглашение")

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
