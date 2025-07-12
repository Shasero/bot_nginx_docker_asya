from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery

import keyboards.keyboard as kb
import database.requests as rq

router = Router()


@router.callback_query(F.data.startswith('keyboarddeletekurs'))
async def deletekurs(callback: CallbackQuery, bot: Bot):
    chat_id = callback.from_user.id
    last_message_id = callback.message.message_id
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
    await callback.message.answer( '⚠️Если вы нажмете на курс, он будет удален!\nВсе курсы в базе:', reply_markup=await kb.delitkeyboardkurs())


@router.callback_query(F.data.startswith('delitkurs_'))
async def kursdelit(callback: CallbackQuery):
    await callback.answer('')
    delit = callback.data.split('_')[1]
    delitintkurs = int(delit)
    await rq.droptablekurs(delitintkurs)
    await callback.message.answer('Курс удален!')