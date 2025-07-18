from aiogram import Router, types, F
from aiogram.filters import Command
import sqlite3
router = Router()

INFO_TEXTS = {
    "requirements": """
<b>Требования к донорам</b>

• Возраст: Не менее 18 лет
• Вес: Не менее 50 кг
• Здоровье:
  - Отсутствие хронических заболеваний в острой фазе
  - Не болели ангиной, ОРВИ, гриппом менее чем за месяц
  - Температура тела ≤ 37°C
  - Давление: систолическое 90-160 мм рт.ст., диастолическое 60-100 мм рт.ст.
  - Гемоглобин: женщины ≥ 120 г/л, мужчины ≥ 130 г/л
• Периодичность:
  - Цельная кровь: мужчины 4-5 раз в год, женщины 3-4 раза в год
""",

    "preparation": """
<b>Подготовка к донации (за 2-3 дня)</b>

• Питание:
  - Исключить жирную, острую, копченую пищу
  - Отказаться от фастфуда, молочных продуктов и яиц
• Образ жизни:
  - Отказ от алкоголя за 48 часов
  - Избегать интенсивных физических нагрузок
  - Отменить прием лекарств за 72 часа
• Накануне:
  - Легкий ужин до 20:00
  - Сон не менее 8 часов
  - Обязательный завтрак (каша на воде, сладкий чай)
  - Не курить за 1 час до сдачи
""",

    "diet": """
<b>Рацион донора за 2-3 дня до донации</b>

• Водный режим: 1.5-2 литра воды в день
• Основа рациона:
  - Крупы на воде
  - Отварное нежирное мясо (говядина, индейка, курица)
  - Белая нежирная рыба (треска, хек)
  - Овощи и фрукты (кроме запрещенных)
• Запрещено:
  - Жирное мясо, молочные продукты, яйца, орехи
  - Фастфуд, копчености, майонез
  - Цитрусовые, бананы, киви, клубника, авокадо, виноград, свекла, шпинат
""",

    "absolute_contra": """
<b>Абсолютные противопоказания</b>

• Инфекционные:
  - ВИЧ/СПИД
  - Сифилис
  - Вирусные гепатиты (B, C)
  - Туберкулез
• Паразитарные:
  - Токсоплазмоз
  - Лейшманиоз
• Онкологические заболевания
• Болезни крови
• Сердечно-сосудистые:
  - Гипертония II-III ст.
  - Ишемическая болезнь
  - Органические поражения ЦНС
  - Бронхиальная астма
""",

    "temp_contra": """
<b>Временные противопоказания</b>

• После заболеваний:
  - ОРВИ, грипп - 1 месяц
  - Ангина - 1 месяц
  - Удаление зуба - 10 дней
  - Менструация + 5 дней
• После процедур:
  - Татуировки/пирсинг - 4-12 месяцев
  - Эндоскопия - 4-6 месяцев
  - Прививки (живые вакцины) - 1 месяц
• Лекарства:
  - Антибиотики - 2 недели после курса
  - Анальгетики - 3 дня после приема
""",

    "bmd_importance": """
<b>Важность донорства костного мозга</b>

Ежегодно в России >5 000 человек нуждаются в трансплантации костного мозга. Только 30-40% находят совместимого донора среди родственников. 

Федеральный регистр доноров костного мозга (ФРДКМ) насчитывает всего ~200 000 человек (2024 г.), что крайне мало для страны с населением 146 млн. 

Для сравнения:
• Германия: 9 млн доноров
• США: 12 млн доноров

Каждый новый донор увеличивает шансы пациентов на спасение жизни!
""",

    "bmd_reg": """
<b>Процедура вступления в регистр доноров костного мозга</b>

1. Первичное согласие:
   - Возраст 18-45 лет
   - Вес >50 кг
   - Отсутствие противопоказаний

2. Забор биоматериала:
   - Вариант 1: Анализ крови (10 мл из вены)
   - Вариант 2: Мазок с внутренней поверхности щеки

3. Типирование:
   - Генетический анализ HLA-фенотипа
   - Данные вносятся в базу ФРДКМ

4. Ожидание:
   - Средний срок: 2-10 лет
   - Вероятность "совпадения": ~5%
   - При совпадении - дополнительное обследование и процедура донации
""",

    "bmd_procedure": """
<b>Процедура донации костного мозга</b>

Способ 1: Периферический забор (80% случаев)
• Подготовка: 5 дней контроля анализов
• Процесс:
  - Забор крови из одной руки
  - Сепарация стволовых клеток
  - Возврат крови через другую руку
• Длительность: 4-6 часов
• Восстановление: 1-2 дня

Способ 2: Пункция костного мозга (20% случаев)
• Подготовка: Полное обследование
• Процесс:
  - Анестезия
  - Прокол тазовых костей иглами
  - Забор 500-1000 мл костного мозга
• Длительность: 1-1.5 часа
• Восстановление: 3-7 дней
"""
}

@router.message(Command("menu"))
async def cmd_start(message: types.Message):
    buttons = [
        [
            types.InlineKeyboardButton(
                text="Что нужно знать?",
                callback_data="what_to_know"
            ),
            types.InlineKeyboardButton(
                text="Зарегистрироваться на ДД",
                callback_data="register_for_dd"
            )
        ],
        [
            types.InlineKeyboardButton(
                text="Обо мне",
                callback_data="about_me"
            )
        ]
    ]


    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        text="<b>Меню</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "what_to_know")
async def what_to_know(callback: types.CallbackQuery):
    # Создаем кнопки для меню информации
    buttons = [
        [types.InlineKeyboardButton(text="Требования к донорам", callback_data="info_requirements")],
        [types.InlineKeyboardButton(text="Подготовка к донации", callback_data="info_preparation")],
        [types.InlineKeyboardButton(text="Рацион донора", callback_data="info_diet")],
        [types.InlineKeyboardButton(text="Абсолютные противопоказания", callback_data="info_absolute_contra")],
        [types.InlineKeyboardButton(text="Временные противопоказания", callback_data="info_temp_contra")],
        [types.InlineKeyboardButton(text="Важность донорства КМ", callback_data="info_bmd_importance")],
        [types.InlineKeyboardButton(text="Вступление в регистр ДКМ", callback_data="info_bmd_reg")],
        [types.InlineKeyboardButton(text="Процедура донации КМ", callback_data="info_bmd_procedure")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    # Редактируем текущее сообщение
    await callback.message.edit_text(
        text="<b>Выберите, что вы хотите знать:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# Хэндлер для информационных кнопок
@router.callback_query(F.data.startswith("info_"))
async def info_handler(callback: types.CallbackQuery):
    # Извлекаем ключ из callback_data (убираем префикс "info_")
    key = callback.data.split("_", 1)[1]
    text = INFO_TEXTS.get(key)

    if text:
        await callback.message.answer(
            text=text,
            parse_mode="HTML"
        )
    else:
        await callback.answer("Информация не найдена")

    await callback.answer()


@router.callback_query(F.data == "about_me")
async def about_me(callback: types.CallbackQuery):
    # Получаем user_id пользователя
    user_id = callback.from_user.id

    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('db.db')
        cursor = conn.cursor()

        # Выполняем запрос к базе данных
        cursor.execute("""
            SELECT Name, GroupID, Gavrilova, FMBA, 
                   LastGavrilov, LastFMBA, Contacts, Phone 
            FROM Donors 
            WHERE UserID = ?
        """, (user_id,))

        user_data = cursor.fetchone()

        if user_data:
            # Распаковываем данные
            (name, group, gavrilova, fmba,
             last_gavrilov, last_fmba, contacts, phone) = user_data

            # Форматируем текст сообщения
            message_text = (
                f"<b>Ваши данные:</b>\n\n"
                f"<b>Имя:</b> {name or 'не указано'}\n"
                f"<b>Группа:</b> {group or 'не указана'}\n"
                f"<b>Контактные данные:</b> {contacts or 'не указаны'}\n"
                f"<b>Телефон:</b> {phone or 'не указан'}\n\n"
                f"<b>Статистика донаций:</b>\n"
                f"• В ЦД Гаврилова: {'да' if gavrilova else 'нет'}\n"
                f"• В ЦД ФМБА: {'да' if fmba else 'нет'}\n"
                f"• Последняя сдача в ЦД Гаврилова: {last_gavrilov or 'нет данных'}\n"
                f"• Последняя сдача в ЦД ФМБА: {last_fmba or 'нет данных'}"
            )
        else:
            message_text = "❌ Ваши данные не найдены в базе доноров."

    except sqlite3.Error as e:
        message_text = f"⚠️ Произошла ошибка при получении данных: {e}"

    finally:
        # Закрываем соединение с базой данных
        if 'conn' in locals():
            conn.close()

    # Отправляем сообщение пользователю
    await callback.message.answer(
        text=message_text,
        parse_mode="HTML"
    )
    await callback.answer()