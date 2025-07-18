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
                                     reply_markup=keyboard_edit_return)

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
        [InlineKeyboardButton(text="баллы Гаврилова", callback_data="edit_Gavrilova")],
        [InlineKeyboardButton(text="баллы FMBA", callback_data="edit_FMBA")],
        [InlineKeyboardButton(text="Последняя дотация в центре Гаврилова", callback_data="edit_LastGavrilov")],
        [InlineKeyboardButton(text="Последняя дотация в центре FMBA", callback_data="edit_LastFMBA")],
        [InlineKeyboardButton(text="Контакты", callback_data="edit_Contacts")],
        [InlineKeyboardButton(text="Внешний донор", callback_data="edit_Stranger")]
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
        "Введите данные доноров (каждая запись с новой строки):\n"
        "Формат: Фамилия,Имя,Отчество,Сотрудник/Группа студента,Телефон\n"
        "Необязательные поля (через запятую):\n"
        "баллы Гаврилова,баллы FMBA,Последняя дотация в центре Гаврилова,\n"
        "Последняя дотация в центре FMBA,Контакты,Внешний донор(0 - нет/1 - да)\n"
        "Тг айди\n\n"
        "Пример минимальных данных:\n"
        "Иванов,Иван,Иванович,Сотрудник,+79161234567\n\n"
        "Пример полных данных:\n"
        "Петров,Пётр,Петрович,Сотрудник,+79261234567,0,1,,2023-02-20,тел.123-456,0,1194604421"
    )
    await state.set_state(states.AddDonorsState.waiting_for_text)


@router.message(states.AddDonorsState.waiting_for_text)
async def handle_text_list(message: Message, state: FSMContext):
    lines = message.text.split('\n')
    added = 0

    async with aiosqlite.connect(db.DATABASE_NAME) as con, con.cursor() as cur:
        for i, line in enumerate(lines, 1):
            try:
                if not line.strip():
                    continue

                parts = [p.strip() for p in line.split(',')]
                print(parts)
                if len(parts) >= 3:
                    full_name = ' '.join(parts[:3])  # Объединяем фамилию, имя и отчество
                    group_id = parts[3]
                    phone = parts[4]

                    # Обработка необязательных полей
                    gavrilova = int(parts[5]) if len(parts) > 5 and parts[5] else 0
                    fmba = int(parts[6]) if len(parts) > 6 and parts[6] else 0
                    last_gavrilov = parts[7] if len(parts) > 7 else None
                    last_fmba = parts[8] if len(parts) > 8 else None
                    contacts = parts[9] if len(parts) > 9 else None
                    stranger = int(parts[10]) if len(parts) > 10 and parts[10] else 0
                    donorsID = int(parts[11]) if len(parts) > 11 and parts[11] else 0

                    await con.execute(
                        """INSERT OR REPLACE INTO Donors
                        (Name, GroupID, Phone,
                         Gavrilova, FMBA, LastGavrilov, LastFMBA, Contacts, Stranger, donorsID)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (full_name, group_id, phone,
                         gavrilova, fmba, last_gavrilov, last_fmba, contacts, stranger, donorsID)
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
async def create_event(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Для создания мероприятия введите дату (dd-mm-yyyy) и "
                                     "центр крови через запятую.\n"
                                     "Каждое мероприятие на новой строчке\n"
                                     "Пример:\n"
                                     "24-03-2024,Гаврилова",
                                     reply_markup=keyboard_return)
    await state.set_state(states.EventState.waiting_for_event)

@router.message(states.EventState.waiting_for_event)
async def select_donor_field(message: Message, state: FSMContext):
    lines = message.text.split('\n')
    added = 0

    async with aiosqlite.connect(db.DATABASE_NAME) as con, con.cursor() as cur:
        for i, line in enumerate(lines, 1):
            try:
                if not line.strip():
                    continue

                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    date = parts[0]
                    donor_center = parts[1]

                    await con.execute(
                        """INSERT OR REPLACE INTO DD
                        (Date, donor_center)
                        VALUES (?, ?)""",
                        (date, donor_center)
                    )
                    added += 1
            except Exception:
                continue

        await con.commit()

    await message.answer(f"✅ Добавлено {added} событий")
    await state.clear()

@router.callback_query(F.data == "upload_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Для загрузки статистики отправьте файл в формате exel",
                                     reply_markup=keyboard_return)

@router.callback_query(F.data == "get_statistics")
async def donor_edit(callback: CallbackQuery):
    await callback.message.edit_text("Вот ваш документ",
                                     reply_markup=keyboard_return)