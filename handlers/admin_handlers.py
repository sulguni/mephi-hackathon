import aiosqlite

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
import states

import db

router = Router()

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


@router.message(Command('admin'), states.IsAdmin())
async def admin_command(message: Message) -> None:
    await message.answer('Добро пожаловать в панель организатора!\n'
                         'Выберите желаемое действие:', reply_markup=keyboard)

@router.callback_query(F.data == "admin_menu")
async def back_to_admin(callback: CallbackQuery):
    await callback.message.edit_text('Добро пожаловать в панель организатора!\n'
                         'Выберите желаемое действие:', reply_markup=keyboard)

kb_edit_return = [
    [InlineKeyboardButton(text="Редактировать пользователя", callback_data='edit_by_phone')],
    [InlineKeyboardButton(text="Добавить пользователей", callback_data='add_user')],
    [InlineKeyboardButton(text="Вернуться", callback_data='admin_menu')]
]
keyboard_edit_return = InlineKeyboardMarkup(inline_keyboard=kb_edit_return)

@router.callback_query(F.data == "donor_edit")
async def donor_edit(callback: CallbackQuery):

    await callback.message.edit_text("Введите номер телефона пользователя, чьи данные вы хотите изменить",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == 'edit_by_phone')
async def start_edit_by_phone(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите номер телефона донора для редактирования:")
    await state.set_state(states.EditDonor.waiting_phone)

@router.message(states.EditDonor.waiting_phone, F.text.regexp(r'^\+?\d{11}$'))
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

@router.callback_query(states.EditDonor.waiting_field, F.data.startswith("edit_"))
async def select_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    await state.update_data(field=field)
    await callback.message.answer(f"Введите новое значение для {field}:")
    await state.set_state(states.EditDonor.waiting_value)
    await callback.answer()


@router.message(states.EditDonor.waiting_value)
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


@router.callback_query(F.data == 'add_user')
async def start_add_donors(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите данные доноров (каждый с новой строки):\n"
        "Формат:\n"
        "ФИО,Группа,Телефон\n"
        "Пример:\n"
        "Иванов Иван Иванович,Сотрудник,+79161234567"
    )
    await state.set_state(states.AddDonorsState.waiting_for_text)


@router.message(states.AddDonorsState.waiting_for_text)
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



@router.callback_query(F.data == "bot_edit")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Выберите, что хотите изменить",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "view_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Статистика:",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "reply_to_questions")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Вопрос:",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "newsletter")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Выберите категорию для рассылки",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "create_event")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Для создания мероприятия введите дату и "
                                     "центр крови",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "upload_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Для загрузки статистики отправьте файл в формате exel",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "get_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Вот ваш документ",
                                     reply_markup=keyboard_return)