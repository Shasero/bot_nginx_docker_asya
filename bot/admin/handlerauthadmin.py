# import asyncio
from aiogram import Router, html, Bot
from aiogram.filters import Command
from aiogram.types import Message
# from aiogram.fsm.state import StatesGroup, State
# from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

import os
from keyboards import keyboard as kb


load_dotenv('/bot/.env')

admin_id = os.getenv('ADMIN_ID')
if admin_id is None:
    raise ValueError("Укажите ADMIN_ID в .env файле!")
else:
    admin_id = int(admin_id)
# intadmin_id = int(admin_id)
admin_id2 = os.getenv('ADMIN_ID2')
if admin_id2 is None:
    raise ValueError("Укажите ADMIN_ID2 в .env файле!")
else:
    admin_id2 = int(admin_id2)
# intadmin_id2 = int(admin_id2)
# login = os.getenv('LOGIN')
# if login is None:
#     raise ValueError("Укажите LOGIN в .env файле!")
# else:
#     admin_id = int(admin_id)
# password = os.getenv('PASSWORD')
# login2 = os.getenv('LOGIN2')
# password2 = os.getenv('PASSWORD2')

router = Router()

# class Auth(StatesGroup):
#     login = State()
#     password = State()


@router.message(Command(commands='adminsettings'))
async def authorization_start(message: Message, bot: Bot):
    if message.from_user.id == admin_id:
        await bot.send_message(message.from_user.id, text=f'Рад вас видеть! {html.bold(message.from_user.full_name)}!', reply_markup=kb.admincompkeyboard)
        return True
    elif message.from_user.id == admin_id2:
        await bot.send_message(message.from_user.id, text=f'Рад вас видеть! {html.bold(message.from_user.full_name)}!', reply_markup=kb.admincompkeyboard)
        return True
    else:
        await bot.send_message(message.from_user.id, 'Эта команда не для вас)')
        return False

# resultplsTrue = asyncio.run(authorization_start(Message, Bot))
# print(resultplsTrue)

# @router.message(Command(commands='adminsettings'))
# async def authorization_start(message: Message, state: FSMContext, bot: Bot):
#     if message.from_user.id == intadmin_id:
#         if message.text != "стоп":
#             await state.set_state(Auth.login)
#             await bot.send_message(message.from_user.id, 'Введите логин: \nДля остановки авторизации введите: стоп')
#         else:
#             await state.clear()
#     elif message.from_user.id == intadmin_id2:
#         if message.text != "стоп":
#             await state.set_state(Auth.login)
#             await bot.send_message(message.from_user.id, 'Введите логин: \nДля остановки авторизации введите: стоп')
#         else:
#             await state.clear()
#     else:
#         await bot.send_message(message.from_user.id, 'Эта команда не для вас)')


# @router.message(Auth.login)
# async def authorization_start2(message: Message, state: FSMContext, bot: Bot):
#     await state.update_data(login=message.text)
#     await state.set_state(Auth.password)
#     if message.text != "стоп":
#         await bot.send_message(message.from_user.id, 'Введите пароль: \nДля остановки авторизации введите: стоп')
#     else:
#         await state.clear()


# @router.message(Auth.password)
# async def authorization_start3(message: Message, state: FSMContext, bot: Bot):
#     try:
#         await state.update_data(password=message.text)
#         data = await state.get_data()
#         logind = data.get('login')
#         passwordd = data.get('password')
#         if login == logind and password == passwordd:
#             await bot.send_message(message.from_user.id, f'Добрый день! {html.bold(message.from_user.full_name)}!', reply_markup=kb.admincompkeyboard)
#             await state.clear()
#         elif login2 == logind and password2 == passwordd:
#             await bot.send_message(message.from_user.id, f'Добрый день! {html.bold(message.from_user.full_name)}!', reply_markup=kb.admincompkeyboard)
#             await state.clear()
#         else:
#             await bot.send_message(message.from_user.id, 'Неверный логин или пароль\nПовторите попытку авторизации ↓')
#             if message.text != "стоп":
#                 await state.clear()
#             else:
#                 await state.clear()
#                 return None
#     except Exception as e:
#         print(f"Ошибка авторизации: {e}")
#         return None


