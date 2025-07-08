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


@router.message(AddGaid.fail, ~F.document)
async def handle_wrong_content_type(message: Message):
    await message.answer(
        "⚠️ Пожалуйста, отправьте файл как документ через меню \"Прикрепить файл\".\n"
        "Если вы отправили файл, но видите это сообщение, попробуйте:\n"
        "1. Нажать на скрепку в поле ввода\n"
        "2. Выбрать \"Документ\"\n"
        "3. Выбрать нужный файл"
    )

# Основной обработчик документа
@router.message(AddGaid.fail, F.document)
async def addfail(message: Message, state: FSMContext, bot: Bot):
    try:
        document = message.document
        
        # Проверка типа файла
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument',
            'application/msword',
            'text/plain'
        ]
        
        if not any(document.mime_type.startswith(t) for t in allowed_types):
            await message.answer(
                "❌ Неподдерживаемый формат файла.\n"
                "Поддерживаются: PDF, Word (docx/doc), текстовые файлы."
            )
            return
        
        # Проверка размера файла (20MB максимум)
        if document.file_size > 20 * 1024 * 1024:
            await message.answer("❌ Файл слишком большой. Максимальный размер - 20MB.")
            return
        
        # Сохраняем информацию о файле
        file_info = {
            'file_id': document.file_id,
            'file_name': document.file_name,
            'file_size': document.file_size,
            'mime_type': document.mime_type
        }
        
        await state.update_data(fail=file_info)
        await state.set_state(AddGaid.pricecardgaid)
        await message.answer(
            f"✅ Файл \"{document.file_name}\" успешно загружен!\n"
            "Теперь укажите цену гайда в рублях:"
        )
        
    except Exception as e:
        logging.error(f"Error processing document: {str(e)}", exc_info=True)
        await message.answer(
            "⚠️ Произошла ошибка при обработке файла. Пожалуйста:\n"
            "1. Проверьте, что файл не поврежден\n"
            "2. Попробуйте отправить его еще раз\n"
            "3. Если ошибка повторяется, попробуйте другой файл"
        )


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