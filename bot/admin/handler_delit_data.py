import logging
import os
import json
import keyboards.keyboard as kb
import database.requests as rq

from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "user_id": getattr(record, 'user_id', None),
            "extra": getattr(record, 'extra', {})
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)



def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    os.makedirs('logs', exist_ok=True)
    
    file_handler = RotatingFileHandler(
        'logs/handler_delit_data.log',
        maxBytes=10*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(JsonFormatter())
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()


router = Router()

class DataDelit:
    def __init__(self, data_type: str):
        self.data_type = data_type


    async def select_data_for_delete(self, callback: CallbackQuery, bot: Bot):
        chat_id = callback.from_user.id
        last_message_id = callback.message.message_id
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
        keyboard_func = getattr(kb, f'delit_keyboard_{self.data_type}')
        data_name = "гайд" if self.data_type == "gaid" else "курс"
        await callback.message.answer(f'⚠️Если вы нажмете на {data_name}, он будет удален!\nВсе {data_name}ы в базе:', reply_markup=await keyboard_func())

    async def delete_data(self, callback: CallbackQuery):
        await callback.answer('')
        selection_id = callback.data.split('_')[1]
        func_delit = getattr(rq, f'get_{self.data_type}')
        items = await func_delit(selection_id)
        for item in items:
            data_name = (
                item.name_fail_gaid if self.data_type == 'gaid' else item.name_fail_kurs
            )
        func_delit = getattr(rq, f'drop_table_{self.data_type}')
        await func_delit(selection_id)
        await callback.message.answer(f'{data_name} удален!')


delit_gaid = DataDelit('gaid')
delit_kurs = DataDelit('kurs')


@router.callback_query(F.data.startswith('keyboard_delete_gaid'))
async def start_on_delit_gaid(callback: CallbackQuery, bot: Bot):
    await delit_gaid.select_data_for_delete(callback, bot)
    
@router.callback_query(F.data.startswith('delitg_'))
async def drop_gaid(callback: CallbackQuery):
    await delit_gaid.delete_data(callback)

@router.callback_query(F.data.startswith('keyboard_delete_kurs'))
async def start_on_delit_kurs(callback: CallbackQuery, bot: Bot):
    await delit_kurs.select_data_for_delete(callback, bot)

@router.callback_query(F.data.startswith('delitk_'))
async def drop_kurs(callback: CallbackQuery):
    await delit_kurs.delete_data(callback)