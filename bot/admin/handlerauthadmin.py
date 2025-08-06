# import asyncio
from aiogram import Router, html, Bot
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

import os
from keyboards import keyboard as kb


load_dotenv('.env')

admin_id = os.getenv('ADMIN_ID')
if admin_id is None:
    raise ValueError("Укажите ADMIN_ID в .env файле!")
else:
    admin_id = int(admin_id)
admin_id2 = os.getenv('ADMIN_ID2')
if admin_id2 is None:
    raise ValueError("Укажите ADMIN_ID2 в .env файле!")
else:
    admin_id2 = int(admin_id2)

router = Router()


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
