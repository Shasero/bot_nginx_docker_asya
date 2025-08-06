from aiogram import Router, html, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

import database.requests as rq


router = Router()


@router.message(CommandStart())
async def start(message: Message, bot: Bot) -> None:
    await rq.set_user(message.from_user.id, message.from_user.full_name)
    await bot.send_message(message.from_user.id, f'Здравствуй! {html.bold(message.from_user.full_name)}!')
    
