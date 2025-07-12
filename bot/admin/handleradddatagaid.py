from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import logging
import sqlite3

import database.requests as rq

router = Router()


class AddGaid(StatesGroup):
    namefail = State()
    photo = State()
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
async def addphoto(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.photo:
            await message.answer("Пожалуйста, добавьте фото.")
            return
        await state.update_data(namefail=message.text)
        await state.set_state(AddGaid.photo)
        await bot.send_message(message.from_user.id, 'Теперь отправьте фото для гайда: ')
    except Exception as e:
        logging.error(f"Error in photo: {e}")
        await message.answer("Ошибка при обработке фото. Попробуйте еще раз.")


@router.message(AddGaid.photo)
async def addnamefail(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text:
            await message.answer("Пожалуйста, добавьте фото.")
            return
        
        if len(message.photo) > 1:
            photo_id = message.photo[-1].file_id  # Берем самое высокое качество
        else:
            photo_id = message.photo[0].file_id

        await state.update_data(photo=photo_id)
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
        "⚠️ Пожалуйста, отправьте файл как документ"
        "Если вы отправили файл, но видите это сообщение, попробуйте:\n"
        "1. Нажать на скрепку в поле ввода\n"
        "2. Выбрать \"Документ\"\n"
        "3. Выбрать нужный файл"
    )


@router.message(AddGaid.fail)
async def addfail(message: Message, state: FSMContext, bot: Bot):
    try:
        if not hasattr(message, 'document') or message.document is None:
            await message.answer(
                "📎 Пожалуйста, отправьте файл через меню \"Прикрепить\" -> \"Документ\"\n"
                "Если вы уже отправили файл, но видите это сообщение, "
                "возможно, файл слишком большой или имеет неподдерживаемый формат."
            )
            return

        document = message.document
        required_attrs = ['file_id', 'file_name', 'mime_type', 'file_size']
        
        if not all(hasattr(document, attr) for attr in required_attrs):
            await message.answer("⚠️ Не удалось получить полную информацию о файле. Попробуйте другой файл.")
            return

        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument',
            'application/msword',
            'text/plain'
        ]
        
        if not document.mime_type or not any(document.mime_type.startswith(t) for t in allowed_types):
            await message.answer(
                "❌ Неподдерживаемый формат файла.\n"
                f"Получен: {document.mime_type or 'неизвестный'}\n"
                "Поддерживаются: PDF, Word (docx/doc), текстовые файлы."
            )
            return
        
        max_size = 20 * 1024 * 1024
        if not document.file_size or document.file_size > max_size:
            await message.answer(
                f"❌ Файл слишком большой. Размер: {document.file_size or 'неизвестный'} байт\n"
                f"Максимальный размер: {max_size} байт (20MB)"
            )
            return
        
        file_info = {
            'file_id': document.file_id,
            'file_name': document.file_name,
            'file_size': document.file_size,
            'mime_type': document.mime_type,
            'date': message.date.isoformat()
        }
        
        await state.update_data(fail=file_info)
        await state.set_state(AddGaid.pricecardgaid)
        
        await message.answer(
            f"✅ Файл успешно принят!\n"
            f"Название: {document.file_name}\n"
            f"Тип: {document.mime_type}\n"
            f"Размер: {round(document.file_size/1024/1024, 2)} MB\n\n"
            "Теперь укажите цену гайда в рублях:"
        )
        
    except Exception as e:
        logging.error(f"Document processing error: {str(e)}", exc_info=True)
        await message.answer(
            "⚠️ Критическая ошибка при обработке файла.\n"
            "Пожалуйста:\n"
            "1. Проверьте, что файл не поврежден\n"
            "2. Попробуйте переименовать файл (только латинские буквы и цифры)\n"
            "3. Попробуйте отправить другой файл\n\n"
            f"Техническая информация: {type(e).__name__}"
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
        logging.error(f"Ошибка в addpricecardgaid: {e}")
        await message.answer("Ошибка при обработке цены. Попробуйте еще раз.")


@router.message(AddGaid.pricestargaid)
async def addpricestargaid(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text or not message.text.isdigit():
            await message.answer("Пожалуйста, укажите корректную цену в звездах (только цифры).")
            return
        
        addata = await state.get_data()
        
        file_info = addata.get('fail', {})
        file_id = file_info.get('file_id', '')
        
        if not all([
            addata.get('namefail'),
            addata.get('photo'),
            addata.get('descriptiongaid'),
            file_id,
            addata.get('pricecardgaid'),
            message.text
        ]):
            await message.answer("Ошибка: отсутствуют необходимые данные. Пожалуйста, начните заново.")
            await state.clear()
            return
        
        await rq.addgaid(
            namefail=addata['namefail'],
            photo=addata['photo'],
            descriptiongaid=addata['descriptiongaid'],
            fail=file_id,
            pricecardgaid=addata['pricecardgaid'],
            pricestargaid=message.text
        )
        
        await message.answer("✅ Данные успешно добавлены!")
        await state.clear()
        
    except sqlite3.ProgrammingError as e:
        logging.error(f"Ошибка базы данных в addpricestargaid: {e}")
        await message.answer("Ошибка при сохранении в базу данных. Пожалуйста, попробуйте снова.")
        await state.clear()
    except Exception as e:
        logging.error(f"Непредвиденная ошибка в addpricestargaid: {e}")
        await message.answer("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()