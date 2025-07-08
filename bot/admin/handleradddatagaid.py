from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import logging

import database.requests as rq

router = Router()


class AddGaid(StatesGroup):
    namefail = State()
    descriptiongaid = State()
    fail = State()
    pricecardgaid = State()
    pricestargaid = State()


@router.callback_query(F.data.startswith('keyboardaddgaid'))
async def addpole(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        chat_id = callback.from_user.id
        last_message_id = callback.message.message_id
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
        await state.set_state(AddGaid.namefail)
        await callback.message.answer('Введите название файла: ')
    except Exception as e:
        logging.error(f"Error in addpole: {e}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")


@router.message(AddGaid.namefail)
async def addnamefail(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text:
            await message.answer("Пожалуйста, введите название файла.")
            return
        await state.update_data(namefail=message.text)
        await state.set_state(AddGaid.descriptiongaid)
        await bot.send_message(message.from_user.id, 'Введите описание: ')
    except Exception as e:
        logging.error(f"Error in addnamefail: {e}")
        await message.answer("Ошибка при обработке названия. Попробуйте еще раз.")


@router.message(AddGaid.descriptiongaid)
async def adddescriptiongaid(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text:
            await message.answer("Пожалуйста, введите описание.")
            return
        await state.update_data(descriptiongaid=message.text)
        await state.set_state(AddGaid.fail)
        await bot.send_message(message.from_user.id, 'Загрузите файл: ')
    except Exception as e:
        logging.error(f"Error in adddescriptiongaid: {e}")
        await message.answer("Ошибка при обработке описания. Попробуйте еще раз.")


@router.message(AddGaid.fail)
async def addfail(message: Message, state: FSMContext, bot: Bot):
    try:
        # Проверяем, что сообщение содержит документ
        if not message.document:
            await message.answer("❌ Пожалуйста, отправьте файл как документ")
            return  # Остаемся в текущем состоянии
        
        # Получаем информацию о файле
        file_info = {
            'file_id': message.document.file_id,
            'file_name': message.document.file_name,
            'mime_type': message.document.mime_type,
            'file_size': message.document.file_size
        }
        
        # Дополнительная проверка типа файла (пример для PDF)
        if not message.document.mime_type.endswith(('pdf', 'vnd.openxmlformats-officedocument')):
            await message.answer("⚠️ Принимаются только PDF или Word документы. Пожалуйста, отправьте файл в правильном формате.")
            return
            
        # Проверка размера файла (например, не более 20MB)
        if message.document.file_size > 20 * 1024 * 1024:
            await message.answer("⚠️ Файл слишком большой. Максимальный размер - 20MB.")
            return
            
        # Сохраняем file_id в состояние
        await state.update_data(fail=file_info)
        
        # Переходим к следующему шагу
        await state.set_state(AddGaid.pricecardgaid)
        await bot.send_message(
            message.from_user.id,
            '✅ Файл успешно принят!\n'
            'Укажите цену гайда в рублях:'
        )
        
    except AttributeError as e:
        logging.error(f"Document processing error: {str(e)}")
        await message.answer("❌ Ошибка при обработке файла. Пожалуйста, попробуйте отправить файл еще раз.")
    except Exception as e:
        logging.error(f"Unexpected error in addfail: {str(e)}")
        await message.answer("⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")


@router.message(AddGaid.pricecardgaid)
async def addpricecardgaid(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text or not message.text.isdigit():
            await message.answer("Пожалуйста, укажите корректную цену в рублях (только цифры).")
            return
        await state.update_data(pricecardgaid=message.text)
        await state.set_state(AddGaid.pricestargaid)
        await bot.send_message(message.from_user.id, 'Укажите цену гайда в звездах: ')
    except Exception as e:
        logging.error(f"Error in addpricecardgaid: {e}")
        await message.answer("Ошибка при обработке цены. Попробуйте еще раз.")


@router.message(AddGaid.pricestargaid)
async def addpricestargaid(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text or not message.text.isdigit():
            await message.answer("Пожалуйста, укажите корректную цену в звездах (только цифры).")
            return
        
        await state.update_data(pricestargaid=message.text)
        addata = await state.get_data()
        namefail = addata.get('namefail')
        descriptiongaid = addata.get('descriptiongaid')
        fail = addata.get('fail')
        pricecardgaid = addata.get('pricecardgaid')
        pricestargaid = addata.get('pricestargaid')
        
        await rq.addgaid(namefail, descriptiongaid, fail, pricecardgaid, pricestargaid)
        await bot.send_message(message.from_user.id, 'Данные добавлены успешно!')
        await state.clear()
    except Exception as e:
        logging.error(f"Error in addpricestargaid: {e}")
        await message.answer("Ошибка при сохранении данных. Пожалуйста, попробуйте снова.")
        await state.clear()