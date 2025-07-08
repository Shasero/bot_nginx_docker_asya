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
@router.message(AddGaid.fail)
async def addfail(message: Message, state: FSMContext, bot: Bot):
    try:
        # Полная проверка документа
        if not hasattr(message, 'document') or message.document is None:
            await message.answer(
                "📎 Пожалуйста, отправьте файл через меню \"Прикрепить\" -> \"Документ\"\n"
                "Если вы уже отправили файл, но видите это сообщение, "
                "возможно, файл слишком большой или имеет неподдерживаемый формат."
            )
            return

        document = message.document
        required_attrs = ['file_id', 'file_name', 'mime_type', 'file_size']
        
        # Проверка наличия всех необходимых атрибутов
        if not all(hasattr(document, attr) for attr in required_attrs):
            await message.answer("⚠️ Не удалось получить полную информацию о файле. Попробуйте другой файл.")
            return

        # Проверка типа файла с защитой от None
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
        
        # Проверка размера файла
        max_size = 20 * 1024 * 1024  # 20MB
        if not document.file_size or document.file_size > max_size:
            await message.answer(
                f"❌ Файл слишком большой. Размер: {document.file_size or 'неизвестный'} байт\n"
                f"Максимальный размер: {max_size} байт (20MB)"
            )
            return
        
        # Сохраняем информацию о файле
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