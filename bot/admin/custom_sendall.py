from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from dotenv import load_dotenv
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import database.requests as rq

router = Router()

load_dotenv()


class Custom_message(StatesGroup):
    msg_custom = State()


@router.callback_query(F.data == 'custom_message')
async def function_custom_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await state.set_state(Custom_message.msg_custom)
    await callback.message.answer(text='Введите ваше сообщение (или отправьте медиа):')


@router.message(Custom_message.msg_custom)
async def get_custom_message(message: Message, state: FSMContext, bot: Bot):
    users = await rq.get_users()
    success_count = 0
    failure_count = 0

    if message.text:
        custom_text = message.text
        for user in users:
            try:
                await bot.send_message(chat_id=user.tg_id, text=custom_text)
                if int(user.active) != 1:
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1

    elif message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption
        for user in users:
            try:
                await bot.send_photo(chat_id=user.tg_id, photo=file_id, caption=caption)
                if int(user.active) != 1:
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке фото пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1

    elif message.video:
        file_id = message.video.file_id
        caption = message.caption
        for user in users:
            try:
                await bot.send_video(chat_id=user.tg_id, video=file_id, caption=caption)
                if int(user.active) != 1:
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке видео пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1

    elif message.document:
        file_id = message.document.file_id
        caption = message.caption
        for user in users:
            try:
                await bot.send_document(chat_id=user.tg_id, document=file_id, caption=caption)
                if int(user.active) != 1:
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
    
    elif message.animation:
        file_id = message.animation.file_id
        caption = message.caption
        for user in users:
            try:
                await bot.send_animation(chat_id=user.tg_id, animation=file_id, caption=caption)
                if int(user.active) != 1:
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке GIF пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1

    elif message.sticker:
        file_id = message.sticker.file_id
        for user in users:
            try:
                await bot.send_sticker(chat_id=user.tg_id, sticker=file_id)
                if int(user.active) != 1:
                    await rq.set_active(user.tg_id, 1)
                success_count += 1
            except TelegramBadRequest as e:
                if "Запрещено: бот заблокирован пользователем" in str(e):
                    await rq.set_active(user.tg_id, 0)
                failure_count += 1
            except Exception as e:
                print(f"Ошибка при отправке стикера пользователю {user.tg_id}: {e}")
                await rq.set_active(user.tg_id, 0)
                failure_count += 1

    else:
        await bot.send_message(message.from_user.id, text='Неподдерживаемый тип сообщения.')
        await state.clear()
        return

    if success_count > 0:
        await bot.send_message(message.from_user.id, text=f'Успешная рассылка. Отправлено {success_count} пользователям. Не удалось отправить {failure_count} пользователям.')
    else:
        await bot.send_message(message.from_user.id, text=f'Не успешная рассылка. Не удалось отправить {failure_count} пользователям.')

    await state.clear()



# from aiogram import F, Router, Bot
# from aiogram.types import CallbackQuery, Message
# from dotenv import load_dotenv
# from aiogram.fsm.state import StatesGroup, State
# from aiogram.fsm.context import FSMContext

# import database.requests as rq

# router = Router()

# load_dotenv()


# class Custom_message(StatesGroup):
#     msg_custom = State()


# @router.callback_query(F.data == 'custom_message')
# async def function_custom_message(callback: CallbackQuery, state: FSMContext):
#     await callback.answer('')
#     await state.set_state(Custom_message.msg_custom)
#     await callback.message.answer(text='Введите ваше сообщение:')


# @router.message(Custom_message.msg_custom)
# async def get_custom_message(message: Message, state: FSMContext, bot: Bot):
#     await state.update_data(msg_custom=message.text)
#     data = await state.get_data()
#     custom = data.get('msg_custom')
#     users = await rq.get_users()
#     for user in users:
#         try:
#             custom_send = await bot.send_message(chat_id=user.tg_id, text=custom)
#             if int(user.active != 1):
#                 await rq.set_active(user.tg_id, 1)
#         except:
#             await rq.set_active(user.tg_id, 0)
#     if custom_send:
#         await bot.send_message(message.from_user.id, text='Успешная расcылка')
#     else:
#         await bot.send_message(message.from_user.id, text='Не успешная рассылка')
#     await state.clear()