from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import logging
import sys
import sqlite3

import database.requests as rq

router = Router()

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("add_data.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  
    ]
)
logger = logging.getLogger(__name__)

# Константы для валидации
MAX_PHOTO_SIZE_MB = 5
MAX_FILE_SIZE_MB = 20
MIN_PRICE = 0
MAX_PRICE = 100000

class AddDataStates(StatesGroup):
    name = State()
    photo = State()
    description = State()
    file = State() 
    price_card = State()
    price_star = State()

class DataType:
    GAID = "gaid"
    KURS = "kurs"

class DataHandler:
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.states = AddDataStates
        self.max_photo_size = MAX_PHOTO_SIZE_MB
        self.max_file_size = MAX_FILE_SIZE_MB
        self.min_price = MIN_PRICE
        self.max_price = MAX_PRICE
        
    async def start_adding(self, callback: CallbackQuery, state: FSMContext, bot: Bot):
        """Начало процесса добавления данных"""
        try:
            logger.info(f"[START] Начало добавления {self.data_type} для пользователя {callback.from_user.id}")
            await state.update_data(data_type=self.data_type)
            chat_id = callback.from_user.id
            last_message_id = callback.message.message_id
            
            await callback.answer()
            await callback.message.edit_reply_markup(reply_markup=None)
            await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
            await state.set_state(self.states.name)
            
            text_map = {
                DataType.GAID: '📝 Введите название гайда:',
                DataType.KURS: '📝 Введите название курса:'
            }
            message_text = text_map[self.data_type]
            print(message_text)
            logger.info(f"[SEND] Отправка сообщения пользователю {chat_id}: {message_text}")
            await callback.message.answer(message_text)
            
        except Exception as e:
            error_msg = f"[ERROR] Ошибка в start_adding для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await callback.message.answer("⚠️ Произошла ошибка. Пожалуйста, попробуйте снова.")

    async def process_name(self, message: Message, state: FSMContext):
        """Обработка названия"""
        try:
            logger.info(f"[PROCESS] Обработка названия для {self.data_type} от пользователя {message.from_user.id}")
            
            if not message.text or len(message.text.strip()) < 3:
                warn_msg = "❌ Название должно содержать минимум 3 символа."
                logger.warning(warn_msg)
                await message.answer(warn_msg)
                return
            
            name = message.text.strip()
            logger.info(f"[CHECK] Проверка уникальности названия: {name}")
            
            try:
                if self.data_type == DataType.GAID:
                    existing_data = await rq.get_gaid(name)
                else:
                    existing_data = await rq.get_kurs(name)
                    
                if existing_data is None:
                    error_msg = "⚠️ Ошибка при проверке уникальности названия."
                    logger.error(error_msg)
                    await message.answer(error_msg)
                    return
                    
                # Проверяем, есть ли уже такой курс/гайд
                try:
                    existing_items = list(existing_data)
                    if existing_items:
                        warn_msg = f"⚠️ Данные с названием '{name}' уже существуют."
                        logger.warning(warn_msg)
                        await message.answer(warn_msg)
                        return
                except Exception as e:
                    error_msg = f"[ERROR] Ошибка при проверке существующих данных: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await message.answer("⚠️ Ошибка при проверке данных. Попробуйте позже.")
                    return
                    
            except Exception as db_error:
                error_msg = f"[ERROR] Ошибка базы данных при проверке уникальности: {str(db_error)}"
                logger.error(error_msg, exc_info=True)
                await message.answer("⚠️ Ошибка при проверке данных. Попробуйте позже.")
                return
                
            await state.update_data(name=name)
            await state.set_state(self.states.photo)
            
            text_map = {
                DataType.GAID: "📸 Теперь отправьте фото для гайда (макс. 5MB):",
                DataType.KURS: "📸 Теперь отправьте фото для курса (макс. 5MB):"
            }
            next_msg = text_map[self.data_type]
            logger.info(f"[NEXT] Переход к состоянию 'photo'. Отправка сообщения: {next_msg}")
            await message.answer(next_msg)
            
        except Exception as e:
            error_msg = f"[ERROR] Ошибка в process_name для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer("⚠️ Ошибка при обработке названия. Попробуйте ещё раз.")

    async def process_photo(self, message: Message, state: FSMContext):
        """Обработка фото"""
        try:
            logger.info(f"[PROCESS] Обработка фото для {self.data_type} от пользователя {message.from_user.id}")
            
            if not message.photo:
                warn_msg = "❌ Пожалуйста, отправьте фото."
                logger.warning(warn_msg)
                await message.answer(warn_msg)
                return
            
            photo = message.photo[-1]
            photo_size_mb = photo.file_size / (1024 * 1024) if photo.file_size else 0
            logger.info(f"[PHOTO] Получено фото. Размер: {photo_size_mb:.1f}MB")
            
            if photo_size_mb > self.max_photo_size:
                warn_msg = f"❌ Фото слишком большое ({photo_size_mb:.1f}MB). Максимальный размер: {self.max_photo_size}MB."
                logger.warning(warn_msg)
                await message.answer(warn_msg)
                return
            
            await state.update_data(photo=photo.file_id)
            await state.set_state(self.states.description)
            
            text_map = {
                DataType.GAID: f"✅ Фото сохранено! (Размер: {photo_size_mb:.1f}MB)\n📝 Теперь введите описание гайда:",
                DataType.KURS: f"✅ Фото сохранено! (Размер: {photo_size_mb:.1f}MB)\n📝 Теперь введите описание курса:"
            }
            next_msg = text_map[self.data_type]
            logger.info(f"[NEXT] Переход к состоянию 'description'. Отправка сообщения: {next_msg}")
            await message.answer(next_msg)
            
        except Exception as e:
            error_msg = f"[ERROR] Ошибка в process_photo для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer("⚠️ Ошибка при обработке фото. Попробуйте ещё раз.")

    async def process_description(self, message: Message, state: FSMContext):
        """Обработка описания"""
        try:
            logger.info(f"[PROCESS] Обработка описания для {self.data_type} от пользователя {message.from_user.id}")
            
            if not message.text or len(message.text.strip()) < 10:
                warn_msg = "❌ Описание должно содержать минимум 10 символов."
                logger.warning(warn_msg)
                await message.answer(warn_msg)
                return
                
            description = message.text.strip()
            logger.info(f"[DESC] Получено описание. Длина: {len(description)} символов")
            await state.update_data(description=description)
            await state.set_state(self.states.file)
            
            text_map = {
                DataType.GAID: "📎 Загрузите файл гайда (макс. 20MB):\nПоддерживаемые форматы: PDF, Word (docx/doc), текстовые файлы.",
                DataType.KURS: "📎 Загрузите файл курса (макс. 20MB):\nПоддерживаемые форматы: PDF, Word (docx/doc), текстовые файлы."
            }
            next_msg = text_map[self.data_type]
            logger.info(f"[NEXT] Переход к состоянию 'file'. Отправка сообщения: {next_msg}")
            await message.answer(next_msg)
            
        except Exception as e:
            error_msg = f"[ERROR] Ошибка в process_description для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer("⚠️ Ошибка при обработке описания. Попробуйте ещё раз.")

    @router.message(AddDataStates.file, ~F.document)
    async def handle_wrong_content_type(self, message: Message):
        """Обработка неправильного типа контента для файла"""
        warn_msg = "Пользователь отправил неподдерживаемый тип контента для файла"
        logger.warning(warn_msg)
        await message.answer(
            "⚠️ Пожалуйста, отправьте файл как документ\n\n"
            "Если вы отправили файл, но видите это сообщение:\n"
            "1. Нажмите на скрепку в поле ввода\n"
            "2. Выберите \"Документ\"\n"
            "3. Выберите нужный файл"
        )

    async def process_file(self, message: Message, state: FSMContext):
        """Обработка файла"""
        try:
            logger.info(f"[PROCESS] Обработка файла для {self.data_type} от пользователя {message.from_user.id}")
            
            if not hasattr(message, 'document') or message.document is None:
                warn_msg = "Пользователь не отправил файл как документ"
                logger.warning(warn_msg)
                await message.answer(
                    "❌ Пожалуйста, отправьте файл через меню \"Прикрепить\" -> \"Документ\"\n"
                    "Если вы уже отправили файл, но видите это сообщение, "
                    "возможно, файл слишком большой или имеет неподдерживаемый формат."
                )
                return

            document = message.document
            required_attrs = ['file_id', 'file_name', 'mime_type', 'file_size']
            logger.info(f"[FILE] Получен документ: {document.file_name} ({document.mime_type})")
            
            if not all(hasattr(document, attr) for attr in required_attrs):
                error_msg = "Не удалось получить полную информацию о файле"
                logger.error(error_msg)
                await message.answer("⚠️ Не удалось получить полную информацию о файле. Попробуйте другой файл.")
                return

            allowed_types = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument',
                'application/msword',
                'text/plain'
            ]
            
            if not document.mime_type or not any(document.mime_type.startswith(t) for t in allowed_types):
                warn_msg = f"Неподдерживаемый формат файла: {document.mime_type or 'неизвестный'}"
                logger.warning(warn_msg)
                await message.answer(
                    "❌ Неподдерживаемый формат файла.\n"
                    f"Получен: {document.mime_type or 'неизвестный'}\n"
                    "Поддерживаются: PDF, Word (docx/doc), текстовые файлы."
                )
                return
            
            max_size = self.max_file_size * 1024 * 1024
            if not document.file_size or document.file_size > max_size:
                warn_msg = f"Файл слишком большой. Размер: {document.file_size or 'неизвестный'} байт"
                logger.warning(warn_msg)
                await message.answer(
                    f"❌ Файл слишком большой. Размер: {document.file_size or 'неизвестный'} байт\n"
                    f"Максимальный размер: {self.max_file_size}MB"
                )
                return
            
            file_info = {
                'file_id': document.file_id,
                'file_name': document.file_name,
                'file_size': document.file_size,
                'mime_type': document.mime_type,
                'date': message.date.isoformat()
            }
            
            logger.info(f"[SAVE] Сохранение информации о файле: {file_info}")
            await state.update_data(file=file_info)
            await state.set_state(self.states.price_card)
            
            file_size_mb = document.file_size / (1024 * 1024)
            next_msg = (
                f"✅ Файл успешно принят!\n"
                f"📄 Название: {document.file_name}\n"
                f"📦 Тип: {document.mime_type}\n"
                f"📏 Размер: {file_size_mb:.1f}MB\n\n"
                "💳 Теперь укажите цену в рублях:"
            )
            logger.info(f"[NEXT] Переход к состоянию 'price_card'. Отправка сообщения: {next_msg}")
            await message.answer(next_msg)
            
        except Exception as e:
            error_msg = f"[ERROR] Критическая ошибка при обработке файла для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer(
                "⚠️ Критическая ошибка при обработке файла.\n"
                "Пожалуйста:\n"
                "1. Проверьте, что файл не поврежден\n"
                "2. Попробуйте переименовать файл (только латинские буквы и цифры)\n"
                "3. Попробуйте отправить другой файл\n\n"
                f"Техническая информация: {type(e).__name__}"
            )

    async def process_price_card(self, message: Message, state: FSMContext):
        """Обработка цены в рублях"""
        try:
            logger.info(f"[PROCESS] Обработка цены в рублях для {self.data_type} от пользователя {message.from_user.id}")
            
            price = message.text.strip()
            logger.info(f"[PRICE] Получена цена: {price}")
            
            if not price.isdigit():
                warn_msg = "Пользователь ввел некорректную цену (не цифры)"
                logger.warning(warn_msg)
                await message.answer("❌ Пожалуйста, укажите корректную цену в рублях (только цифры).")
                return
                
            price = int(price)
            if price < self.min_price or price > self.max_price:
                warn_msg = f"Цена {price} вне допустимого диапазона ({self.min_price}-{self.max_price})"
                logger.warning(warn_msg)
                await message.answer(
                    f"❌ Цена должна быть от {self.min_price} до {self.max_price} рублей.\n"
                    "Пожалуйста, введите корректное значение."
                )
                return
                
            await state.update_data(price_card=str(price))
            await state.set_state(self.states.price_star)
            
            text_map = {
                DataType.GAID: f"✅ Цена в рублях: {price}₽\n⭐ Теперь укажите цену гайда в звездах:",
                DataType.KURS: f"✅ Цена в рублях: {price}₽\n⭐ Теперь укажите цену курса в звездах:"
            }
            next_msg = text_map[self.data_type]
            logger.info(f"[NEXT] Переход к состоянию 'price_star'. Отправка сообщения: {next_msg}")
            await message.answer(next_msg)
            
        except Exception as e:
            error_msg = f"[ERROR] Ошибка в process_price_card для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer("⚠️ Ошибка при обработке цены. Попробуйте ещё раз.")

    async def process_price_star(self, message: Message, state: FSMContext):
        """Обработка цены в звездах и сохранение данных"""
        try:
            data = await state.get_data()
            logger.info(f"[PROCESS] Обработка цены в звездах для {self.data_type}. Текущие данные: {data}")
            
            stars = message.text.strip()
            logger.info(f"[STARS] Получено количество звезд: {stars}")
            
            if not stars.isdigit():
                warn_msg = "Пользователь ввел некорректное количество звезд (не цифры)"
                logger.warning(warn_msg)
                await message.answer("❌ Пожалуйста, укажите корректную цену в звёздах (только цифры).")
                return
                
            stars = int(stars)
            if stars < self.min_price or stars > self.max_price:
                warn_msg = f"Количество звезд {stars} вне допустимого диапазона ({self.min_price}-{self.max_price})"
                logger.warning(warn_msg)
                await message.answer(
                    f"❌ Количество звезд должно быть от {self.min_price} до {self.max_price}.\n"
                    "Пожалуйста, введите корректное значение."
                )
                return
            
            # Проверка всех обязательных полей
            required_fields = {
                'name': "Название",
                'photo': "Фото",
                'description': "Описание",
                'file': "Файл",
                'price_card': "Цена в рублях"
            }
            
            missing_fields = []
            for field, name in required_fields.items():
                if field not in data or not data[field]:
                    missing_fields.append(name)
            
            if missing_fields:
                error_msg = f"Отсутствуют обязательные данные: {missing_fields}"
                logger.error(error_msg)
                await message.answer(f"❌ {error_msg}\nПожалуйста, начните процесс заново.")
                await state.clear()
                return
            
            # Сохранение в базу данных
            try:
                file_info = data.get('file', {})
                file_id = file_info.get('file_id') if isinstance(file_info, dict) else file_info
                
                if self.data_type == DataType.GAID:
                    logger.info(f"[SAVE] Сохранение гайда в БД: {data['name']}")
                    await rq.add_gaid(
                        name_fail_gaid=data['name'],
                        photo_gaid=data['photo'],
                        description_gaid=data['description'],
                        fail_gaid=file_id,
                        price_card_gaid=data['price_card'],
                        price_star_gaid=str(stars)
                    )
                    success_msg = (
                        "✅ Гайд успешно добавлен!\n\n"
                        f"📌 Название: {data['name']}\n"
                        f"📝 Описание: {data['description'][:50]}...\n"
                        f"💳 Цена: {data['price_card']}₽\n"
                        f"⭐ Звёзды: {stars}\n\n"
                        "Спасибо за добавление гайда!"
                    )
                else:
                    logger.info(f"[SAVE] Сохранение курса в БД: {data['name']}")
                    await rq.add_kurs(
                        name_fail_kurs=data['name'],
                        photo_kurs=data['photo'],
                        description_kurs=data['description'],
                        fail_kurs=file_id,  
                        price_card_kurs=data['price_card'],
                        price_star_kurs=str(stars)
                    )
                    success_msg = (
                        "✅ Курс успешно добавлен!\n\n"
                        f"📌 Название: {data['name']}\n"
                        f"📝 Описание: {data['description'][:50]}...\n"
                        f"💳 Цена: {data['price_card']}₽\n"
                        f"⭐ Звёзды: {stars}\n\n"
                        "Спасибо за добавление курса!"
                    )
                
                logger.info(f"[SUCCESS] Успешное сохранение {self.data_type}")
                await message.answer(success_msg)
                await state.clear()
                
            except sqlite3.IntegrityError as e:
                error_msg = f"[ERROR] Ошибка целостности БД при сохранении {self.data_type}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await message.answer(
                    "⚠️ Ошибка: данные с таким названием уже существуют или данные некорректны.\n"
                    "Пожалуйста, начните процесс заново."
                )
                await state.clear()
                
        except sqlite3.ProgrammingError as e:
            error_msg = f"[ERROR] Ошибка программирования БД в process_price_star для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer("⚠️ Ошибка при сохранении в базу данных. Пожалуйста, попробуйте снова.")
            await state.clear()
        except Exception as e:
            error_msg = f"[ERROR] Неожиданная ошибка в process_price_star для {self.data_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await message.answer("⚠️ Произошла ошибка при сохранении. Пожалуйста, попробуйте снова.")
            await state.clear()

# Создаем экземпляры обработчиков для гайдов и курсов
gaid_handler = DataHandler(DataType.GAID)
kurs_handler = DataHandler(DataType.KURS)

# Регистрируем обработчики для гайдов
@router.callback_query(F.data.startswith('keyboardaddgaid'))
async def add_gaid(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logger.info(f"[START] Начало добавления гайда. Пользователь: {callback.from_user.id}")
    await state.update_data(data_type=DataType.GAID)  
    await gaid_handler.start_adding(callback, state, bot)


@router.callback_query(F.data.startswith('keyboardaddkurs'))
async def add_kurs(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logger.info(f"[START] Начало добавления курса. Пользователь: {callback.from_user.id}")
    await state.update_data(data_type=DataType.KURS)
    await kurs_handler.start_adding(callback, state, bot)


@router.message(AddDataStates.name, F.text)
async def add_gaid_name(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(f"[PROCESS] Обработка названия данных. Текущие данные: {data}")
    if data.get('data_type') == DataType.GAID:
        await gaid_handler.process_name(message, state)
    elif data.get('data_type') == DataType.KURS:
        await kurs_handler.process_name(message, state)

@router.message(AddDataStates.photo, F.photo)
async def add_gaid_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(f"[PROCESS] Обработка фото данных. Текущие данные: {data}")
    if data.get('data_type') == DataType.GAID:
        await gaid_handler.process_photo(message, state)
    elif data.get('data_type') == DataType.KURS:
        await kurs_handler.process_photo(message, state)

@router.message(AddDataStates.description, F.text)
async def add_gaid_description(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(f"[PROCESS] Обработка описания данных. Текущие данные: {data}")
    if data.get('data_type') == DataType.GAID:
        await gaid_handler.process_description(message, state)
    elif data.get('data_type') == DataType.KURS:
        await kurs_handler.process_description(message, state)

@router.message(AddDataStates.file, F.document)
async def add_gaid_file(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(f"[PROCESS] Обработка файла данных. Текущие данные: {data}")
    if data.get('data_type') == DataType.GAID:
        await gaid_handler.process_file(message, state)
    elif data.get('data_type') == DataType.KURS:
        await kurs_handler.process_file(message, state)

@router.message(AddDataStates.price_card, F.text)
async def add_gaid_price_card(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(f"[PROCESS] Обработка цены в рублях для данных. Текущие данные: {data}")
    if data.get('data_type') == DataType.GAID:
        await gaid_handler.process_price_card(message, state)
    elif data.get('data_type') == DataType.KURS:
        await kurs_handler.process_price_card(message, state)

@router.message(AddDataStates.price_star, F.text)
async def add_gaid_price_star(message: Message, state: FSMContext):
    data = await state.get_data()
    logger.info(f"[PROCESS] Обработка цены в звездах для данных. Текущие данные: {data}")
    if data.get('data_type') == DataType.GAID:
        await gaid_handler.process_price_star(message, state)
    elif data.get('data_type') == DataType.KURS:
        await kurs_handler.process_price_star(message, state)