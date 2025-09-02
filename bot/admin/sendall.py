from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

import os

import database.requests as rq
import keyboards.keyboard as kb

router = Router()

load_dotenv()


admin_id = os.getenv('ADMIN_ID')
intadmin_id = int(admin_id)
admin_id2 = os.getenv('ADMIN_ID2')
intadmin_id2 = int(admin_id2)


@router.callback_query(F.data.startswith('keyboardrassilka'))
async def rassilka(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(text='Выберите что хотите отправить:', reply_markup=kb.list)


@router.callback_query(F.data == 'sendkurs')
async def kurs(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer(text='Все курсы в базе:', reply_markup=await kb.sendkeyboardkurs())


@router.callback_query(F.data.startswith('sendkurs_'))
async def kurssendall(callback: CallbackQuery, bot: Bot):
    await callback.answer('')
    success_count = 0
    failure_count = 0
    selectkurs = callback.data.split('_')[1]
    kurssel = await rq.get_kurs(selectkurs)
    users = await rq.get_users()
    for kurs in kurssel:
        for user in users:
            try:
                await bot.send_photo(chat_id=user.tg_id, photo=kurs.photo_kurs, caption=kurs.description_kurs)
                await bot.send_document(chat_id=user.tg_id, document=kurs.fail_kurs, caption=kurs.name_fail_kurs)
                if int(user.active != 1):
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке документа пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1
    
    if success_count > 0:
        await callback.message.answer(text=f'Успешная рассылка. Отправлено {success_count} пользователям. Не удалось отправить {failure_count} пользователям.')
    else:
        await callback.message.answer(text=f'Не успешная рассылка. Не удалось отправить {failure_count} пользователям.')


@router.callback_query(F.data == 'sendgaids')
async def gaids(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer('Все гайды в базе:', reply_markup=await kb.sendkeyboardgaid())


@router.callback_query(F.data.startswith('sendgaid_'))
async def gaidsendall(callback: CallbackQuery, bot: Bot):
    await callback.answer('')
    success_count = 0
    failure_count = 0
    getgaid = callback.data.split('_')[1]
    gaidsel = await rq.get_gaid(getgaid)
    users = await rq.get_users()
    for gaid in gaidsel:
        for user in users:
            try:
                await bot.send_photo(chat_id=user.tg_id, photo=gaid.photo_gaid, caption=gaid.description_gaid)
                await bot.send_document(chat_id=user.tg_id, document=gaid.fail_gaid, caption=gaid.name_fail_gaid)
                if int(user.active != 1):
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке документа пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1

    if success_count > 0:
        await callback.message.answer(text=f'Успешная рассылка. Отправлено {success_count} пользователям. Не удалось отправить {failure_count} пользователям.')
    else:
        await callback.message.answer(text=f'Не успешная рассылка. Не удалось отправить {failure_count} пользователям.')
