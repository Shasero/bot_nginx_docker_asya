<<<<<<< HEAD
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton)
=======
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)
>>>>>>> upgrade/main

from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import select_gaid, select_kurs

admincompkeyboard = InlineKeyboardMarkup(inline_keyboard=[
<<<<<<< HEAD
    [InlineKeyboardButton(text='Добавить гайд', callback_data='keyboardaddgaid')], [InlineKeyboardButton(text='Добавить курс', callback_data='keyboardaddkurs')], [InlineKeyboardButton(text='Удалить гайд', callback_data='keyboarddeletegaid')], [InlineKeyboardButton(text='Удалить курс', callback_data='keyboarddeletekurs')],
=======
    [InlineKeyboardButton(text='Добавить гайд', callback_data='keyboardaddgaid')], [InlineKeyboardButton(text='Добавить курс', callback_data='keyboardaddkurs')], [InlineKeyboardButton(text='Удалить гайд', callback_data='keyboard_delete_gaid')], [InlineKeyboardButton(text='Удалить курс', callback_data='keyboard_delete_kurs')],
>>>>>>> upgrade/main
    [InlineKeyboardButton(text='Статистика', callback_data='keyboardstatistika')], [InlineKeyboardButton(text='Рассылка', callback_data='keyboardrassilka')]
])


list = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Курсы', callback_data='sendkurs')],
    [InlineKeyboardButton(text='Гайды', callback_data='sendgaids')],
    [InlineKeyboardButton(text='Ваше сообщение', callback_data='custom_message')]
])


payment_keyboard_gaid = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оплата ⭐️', callback_data='stars_gaid', pay=True)],
    [InlineKeyboardButton(text='Оплата 💳', callback_data='cards_gaid', pay=True)]
], resize_keyboard=True)


payment_keyboard_kurs = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оплата ⭐️', callback_data='stars_kurs', pay=True)],
    [InlineKeyboardButton(text='Оплата 💳', callback_data='cards_kurs', pay=True)]
], resize_keyboard=True)


succsefull_keyboard_gaid = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подтверждаю ✅', callback_data='true_gaid')],
    [InlineKeyboardButton(text='Не подтверждаю ❌', callback_data='false_gaid')]
], resize_keyboard=True)


confirmation_gaid = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да ✅', callback_data='ok_gaid')],
    [InlineKeyboardButton(text='Нет ❌', callback_data='no_gaid')]
], resize_keyboard=True)


confirmation_false_gaid = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да ✅', callback_data='yes_false_gaid')],
    [InlineKeyboardButton(text='Нет ❌', callback_data='no_false_gaid')]
], resize_keyboard=True)


succsefull_keyboard_kurs = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подтверждаю ✅', callback_data='true_kurs')],
    [InlineKeyboardButton(text='Не подтверждаю ❌', callback_data='false_kurs')]
], resize_keyboard=True)


confirmation_kurs = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да ✅', callback_data='ok_kurs')],
    [InlineKeyboardButton(text='Нет ❌', callback_data='no_kurs')]
], resize_keyboard=True)


confirmation_false_kurs = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да ✅', callback_data='yes_false_kurs')],
    [InlineKeyboardButton(text='Нет ❌', callback_data='no_false_kurs')]
], resize_keyboard=True)



async def selectkeyboardgaid():
    all_gaid = await select_gaid()
    keyboard = InlineKeyboardBuilder()
    for gaid in all_gaid:
<<<<<<< HEAD
        keyboard.add(InlineKeyboardButton(text=gaid.namefail, callback_data=f"selectgaid_{gaid.namefail}"))
=======
        keyboard.add(InlineKeyboardButton(text=gaid.name_fail_gaid, callback_data=f"selectgaid_{gaid.name_fail_gaid}"))
>>>>>>> upgrade/main
    return keyboard.adjust(2).as_markup()


async def selectkeyboardkurs():
    all_kurs = await select_kurs()
    keyboard = InlineKeyboardBuilder()
    for kurs in all_kurs:
<<<<<<< HEAD
        keyboard.add(InlineKeyboardButton(text=kurs.nameurl, callback_data=f"selectkurs_{kurs.nameurl}"))
=======
        keyboard.add(InlineKeyboardButton(text=kurs.name_fail_kurs, callback_data=f"selectkurs_{kurs.name_fail_kurs}"))
>>>>>>> upgrade/main
    return keyboard.adjust(2).as_markup()


async def sendkeyboardkurs():
    all_kurs = await select_kurs()
    keyboard = InlineKeyboardBuilder()
    for kurs in all_kurs:
<<<<<<< HEAD
        keyboard.add(InlineKeyboardButton(text=kurs.nameurl, callback_data=f"sendkurs_{kurs.nameurl}"))
=======
        keyboard.add(InlineKeyboardButton(text=kurs.name_fail_kurs, callback_data=f"sendkurs_{kurs.name_fail_kurs}"))
>>>>>>> upgrade/main
    return keyboard.adjust(2).as_markup()


async def sendkeyboardgaid():
    all_gaid = await select_gaid()
    keyboard = InlineKeyboardBuilder()
    for gaid in all_gaid:
<<<<<<< HEAD
        keyboard.add(InlineKeyboardButton(text=gaid.namefail, callback_data=f"sendgaid_{gaid.namefail}"))
    return keyboard.adjust(2).as_markup()


async def delitkeyboardgaid():
    all_gaid = await select_gaid()
    keyboard = InlineKeyboardBuilder()
    for gaid in all_gaid:
        keyboard.add(InlineKeyboardButton(text=gaid.namefail, callback_data=f"delitgaid_{gaid.id}"))
    return keyboard.adjust(2).as_markup()


async def delitkeyboardkurs():
    all_kurs = await select_kurs()
    keyboard = InlineKeyboardBuilder()
    for kurs in all_kurs:
        keyboard.add(InlineKeyboardButton(text=kurs.nameurl, callback_data=f"delitkurs_{kurs.id}"))
=======
        keyboard.add(InlineKeyboardButton(text=gaid.name_fail_gaid, callback_data=f"sendgaid_{gaid.name_fail_gaid}"))
    return keyboard.adjust(2).as_markup()


async def delit_keyboard_gaid():
    all_gaid = await select_gaid()
    keyboard = InlineKeyboardBuilder()
    for gaid in all_gaid:
        keyboard.add(InlineKeyboardButton(text=gaid.name_fail_gaid, callback_data=f"delitg_{gaid.name_fail_gaid}"))
    return keyboard.adjust(2).as_markup()


async def delit_keyboard_kurs():
    all_kurs = await select_kurs()
    keyboard = InlineKeyboardBuilder()
    for kurs in all_kurs:
        keyboard.add(InlineKeyboardButton(text=kurs.name_fail_kurs, callback_data=f"delitk_{kurs.name_fail_kurs}"))
>>>>>>> upgrade/main
    return keyboard.adjust(2).as_markup()
