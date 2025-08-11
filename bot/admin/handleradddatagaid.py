from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import logging
import sqlite3
from datetime import datetime

import database.requests as rq

router = Router()

# Константы для валидации
MAX_PHOTO_SIZE_MB = 5
MAX_FILE_SIZE_MB = 20
MIN_PRICE = 0
MAX_PRICE = 100000

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
        await callback.message.answer('📝 Введите название гайда:')
    except Exception as e:
        logging.error(f"Error in addpole: {e}")
        await callback.message.answer("⚠️ Произошла ошибка. Пожалуйста, попробуйте снова.")


@router.message(AddGaid.namefail)
async def addnamefail(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text or len(message.text.strip()) < 3:
            await message.answer("❌ Название гайда должно содержать минимум 3 символа.")
            return
        
        # Проверка на уникальность названия
        existing_gaid = await rq.get_gaid(message.text.strip())
        if existing_gaid and existing_gaid.first() is not None:
            await message.answer("⚠️ Гайд с таким названием уже существует. Пожалуйста, придумайте другое название.")
            return
            
        await state.update_data(namefail=message.text.strip())
        await state.set_state(AddGaid.photo)
        await message.answer("📸 Теперь отправьте фото для гайда (макс. 5MB):")
    except Exception as e:
        logging.error(f"Error in addnamefail: {e}")
        await message.answer("⚠️ Ошибка при обработке названия. Попробуйте ещё раз.")


@router.message(AddGaid.photo)
async def addphoto(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.photo:
            await message.answer("❌ Пожалуйста, отправьте фото.")
            return
        
        photo = message.photo[-1]  # Берём фото наивысшего качества
        
        # Проверка размера фото
        photo_size_mb = photo.file_size / (1024 * 1024) if photo.file_size else 0
        if photo_size_mb > MAX_PHOTO_SIZE_MB:
            await message.answer(
                f"❌ Фото слишком большое ({photo_size_mb:.1f}MB). "
                f"Максимальный размер: {MAX_PHOTO_SIZE_MB}MB."
            )
            return
        
        await state.update_data(photo=photo.file_id)
        await state.set_state(AddGaid.descriptiongaid)
        await message.answer(
            f"✅ Фото сохранено! (Размер: {photo_size_mb:.1f}MB)\n"
            "📝 Теперь введите описание гайда:"
        )
    except Exception as e:
        logging.error(f"Error in addphoto: {e}", exc_info=True)
        await message.answer("⚠️ Ошибка при обработке фото. Попробуйте ещё раз.")


@router.message(AddGaid.descriptiongaid)
async def adddescriptiongaid(message: Message, state: FSMContext, bot: Bot):
    try:
        if not message.text or len(message.text.strip()) < 10:
            await message.answer("❌ Описание должно содержать минимум 10 символов.")
            return
            
        await state.update_data(descriptiongaid=message.text.strip())
        await state.set_state(AddGaid.fail)
        await message.answer(
            "📎 Загрузите файл гайда (макс. 20MB):\n"
            "Поддерживаемые форматы: PDF, Word (docx/doc), текстовые файлы."
        )
    except Exception as e:
        logging.error(f"Error in adddescriptiongaid: {e}")
        await message.answer("⚠️ Ошибка при обработке описания. Попробуйте ещё раз.")


@router.message(AddGaid.fail, ~F.document)
async def handle_wrong_content_type(message: Message):
    await message.answer(
        "⚠️ Пожалуйста, отправьте файл как документ\n\n"
        "Если вы отправили файл, но видите это сообщение:\n"
        "1. Нажмите на скрепку в поле ввода\n"
        "2. Выберите \"Документ\"\n"
        "3. Выберите нужный файл"
    )


@router.message(AddGaid.fail)
async def addfail(message: Message, state: FSMContext, bot: Bot):
    try:
        if not hasattr(message, 'document') or message.document is None:
            await message.answer(
                "❌ Пожалуйста, отправьте файл через меню \"Прикрепить\" -> \"Документ\"\n"
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
        
        max_size = MAX_FILE_SIZE_MB * 1024 * 1024
        if not document.file_size or document.file_size > max_size:
            await message.answer(
                f"❌ Файл слишком большой. Размер: {document.file_size or 'неизвестный'} байт\n"
                f"Максимальный размер: {MAX_FILE_SIZE_MB}MB"
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
        
        file_size_mb = document.file_size / (1024 * 1024)
        await message.answer(
            f"✅ Файл успешно принят!\n"
            f"📄 Название: {document.file_name}\n"
            f"📦 Тип: {document.mime_type}\n"
            f"📏 Размер: {file_size_mb:.1f}MB\n\n"
            "💳 Теперь укажите цену гайда в рублях:"
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
        price = message.text.strip()
        
        if not price.isdigit():
            await message.answer("❌ Пожалуйста, укажите корректную цену в рублях (только цифры).")
            return
            
        price = int(price)
        if price < MIN_PRICE or price > MAX_PRICE:
            await message.answer(
                f"❌ Цена должна быть от {MIN_PRICE} до {MAX_PRICE} рублей.\n"
                "Пожалуйста, введите корректное значение."
            )
            return
            
        await state.update_data(pricecardgaid=str(price))
        await state.set_state(AddGaid.pricestargaid)
        await message.answer(
            f"✅ Цена в рублях: {price}₽\n"
            "⭐ Теперь укажите цену гайда в звездах:"
        )
    except Exception as e:
        logging.error(f"Ошибка в addpricecardgaid: {e}")
        await message.answer("⚠️ Ошибка при обработке цены. Попробуйте ещё раз.")


@router.message(AddGaid.pricestargaid)
async def addpricestargaid(message: Message, state: FSMContext, bot: Bot):
    try:
        stars = message.text.strip()
        
        if not stars.isdigit():
            await message.answer("❌ Пожалуйста, укажите корректную цену в звёздах (только цифры).")
            return
            
        stars = int(stars)
        if stars < MIN_PRICE or stars > MAX_PRICE:
            await message.answer(
                f"❌ Количество звезд должно быть от {MIN_PRICE} до {MAX_PRICE}.\n"
                "Пожалуйста, введите корректное значение."
            )
            return
        
        data = await state.get_data()
        
        # Детальная проверка всех полей с логированием
        required_fields = {
            'namefail': "Название гайда",
            'photo': "Фото гайда",
            'descriptiongaid': "Описание гайда",
            'fail': "Файл гайда",
            'pricecardgaid': "Цена в рублях"
        }
        
        missing_fields = []
        for field, name in required_fields.items():
            if field not in data or not data[field]:
                missing_fields.append(name)
        
        if missing_fields:
            error_msg = "Отсутствуют обязательные данные:\n- " + "\n- ".join(missing_fields)
            logging.error(f"Missing data in state: {missing_fields}")
            await message.answer(f"❌ {error_msg}\nПожалуйста, начните процесс заново.")
            await state.clear()
            return
        
        # Получаем file_id из словаря или как строку
        file_info = data.get('fail', {})
        file_id = file_info.get('file_id') if isinstance(file_info, dict) else file_info
        
        # Сохранение в базу
        try:
            await rq.addgaid(
                namefail=data['namefail'],
                photo=data['photo'],
                descriptiongaid=data['descriptiongaid'],
                fail=file_id,
                pricecardgaid=data['pricecardgaid'],
                pricestargaid=str(stars),
                created_at=datetime.now().isoformat()
            )
            
            await message.answer(
                "✅ Гайд успешно добавлен!\n\n"
                f"📌 Название: {data['namefail']}\n"
                f"📝 Описание: {data['descriptiongaid'][:50]}...\n"
                f"💳 Цена: {data['pricecardgaid']}₽\n"
                f"⭐ Звёзды: {stars}\n\n"
                "Спасибо за добавление гайда!"
            )
            await state.clear()
            
        except sqlite3.IntegrityError as e:
            logging.error(f"Database integrity error: {e}")
            await message.answer(
                "⚠️ Ошибка: гайд с таким названием уже существует или данные некорректны.\n"
                "Пожалуйста, начните процесс заново."
            )
            await state.clear()
            
    except sqlite3.ProgrammingError as e:
        logging.error(f"Ошибка базы данных в addpricestargaid: {e}")
        await message.answer("⚠️ Ошибка при сохранении в базу данных. Пожалуйста, попробуйте снова.")
        await state.clear()
    except Exception as e:
        logging.error(f"Error in addpricestargaid: {str(e)}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при сохранении. Пожалуйста, попробуйте снова.")
        await state.clear()