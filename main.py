import asyncio
import logging
import re
import sys
from os import getenv
import aiosqlite
from aiogram import Router
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

kb_edit_return = [
    [InlineKeyboardButton(text="Редактировать пользователя", callback_data='edit_by_phone')],
    [InlineKeyboardButton(text="Добавить пользователей", callback_data='add_user')],
    [InlineKeyboardButton(text="Вернуться", callback_data='admin_menu')]
]
keyboard_edit_return = InlineKeyboardMarkup(inline_keyboard=kb_edit_return)

@dp.callback_query(F.data == "donor_edit")
async def donor_edit(callback: CallbackQuery):

    await callback.message.edit_text("Введите номер телефона пользователя, чьи данные вы хотите изменить",
                                     reply_markup=keyboard_return)

@dp.callback_query(F.data == 'edit_by_phone')
async def start_edit_by_phone(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите номер телефона донора для редактирования:")
    await state.set_state(states.EditDonor.waiting_phone)

@dp.message(states.EditDonor.waiting_phone, F.text.regexp(r'^\+?\d{11}$'))
async def select_donor_field(message: Message, state: FSMContext):
    buttons = [
        [InlineKeyboardButton(text="ФИО", callback_data="edit_Name")],
        [InlineKeyboardButton(text="Группа", callback_data="edit_GroupID")],
        [InlineKeyboardButton(text="Контакты", callback_data="edit_Contacts")],
    ]
    get_edit_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)


    await state.update_data(phone=message.text.strip())
    await message.answer("Выберите поле для редактирования:", reply_markup=get_edit_keyboard)
    await state.set_state(states.EditDonor.waiting_field)

@dp.callback_query(states.EditDonor.waiting_field, F.data.startswith("edit_"))
async def select_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    await state.update_data(field=field)
    await callback.message.answer(f"Введите новое значение для {field}:")
    await state.set_state(states.EditDonor.waiting_value)
    await callback.answer()


@dp.message(states.EditDonor.waiting_value)
async def save_changes(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        async with aiosqlite.connect(db.DATABASE_NAME) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"UPDATE Donors SET {data['field']} = ? WHERE Phone = ?",
                    (message.text, data['phone'])
                )

                await conn.commit()


                if cursor.rowcount > 0:
                    await message.answer("✅ Данные успешно обновлены!")
                else:
                    await message.answer("⚠️ Донор с таким номером не найден или данные не изменились")

    except aiosqlite.Error as e:
        await message.answer(f"❌ Ошибка базы данных: {e}")
    finally:
        await state.clear()


@dp.callback_query(F.data == 'add_user')
async def start_add_donors(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите данные доноров (каждый с новой строки):\n"
        "Формат:\n"
        "ФИО,Группа,Телефон\n"
        "Пример:\n"
        "Иванов Иван Иванович,Сотрудник,+79161234567"
    )
    await state.set_state(states.AddDonorsState.waiting_for_text)


@dp.message(states.AddDonorsState.waiting_for_text)
async def handle_text_list(message: Message, state: FSMContext):
    lines = message.text.split('\n')
    added = 0

    async with aiosqlite.connect(db.DATABASE_NAME) as con, con.cursor() as cur:
        for line in lines:
            try:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    print(parts)
                    await con.execute(
                        """INSERT OR REPLACE INTO Donors(Name, GroupID, Phone) 
                        VALUES (?, ?, ?)""",
                        (parts[0], parts[1], parts[2])
                    )
                    added += 1
            except Exception:
                continue

        await con.commit()

    await message.answer(f"✅ Добавлено {added} доноров")
    await state.clear()


kb_return = [
    [InlineKeyboardButton(text="Вернуться", callback_data='admin_menu')]]
keyboard_return = InlineKeyboardMarkup(inline_keyboard=kb_return)



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
