from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery

import keyboards.keyboard as kb
import database.requests as rq

router = Router()


@router.callback_query(F.data.startswith('keyboarddeletegaid'))
async def deletegaid(callback: CallbackQuery, bot: Bot):
    chat_id = callback.from_user.id
    last_message_id = callback.message.message_id
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
    await callback.message.answer( '⚠️Если вы нажмете на гайд, он будет удален!\nВсе гайды в базе:', reply_markup=await kb.delitkeyboardgaid())


@router.callback_query(F.data.startswith('delitgaid_'))
async def gaiddelit(callback: CallbackQuery):
    await callback.answer('')
    delit = callback.data.split('_')[1]
    delitintgaid = int(delit)
    await rq.droptablegaid(delitintgaid)
    await callback.message.answer('Гайд удален!')