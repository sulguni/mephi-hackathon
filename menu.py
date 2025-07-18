from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
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