import logging
import json
import os
import time
import asyncio
import transliterate
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from aiogram import F, Router, html, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

import keyboards.keyboard as kb
import database.requests as rq

# Настройка логгера
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
        'logs/handler_output_data.log',
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

# Декоратор для логирования действий пользователя
def log_user_action(func):
    async def wrapper(*args, **kwargs):
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in func.__annotations__}
        message_or_callback = args[0]
        user_id = getattr(message_or_callback.from_user, 'id', None)
        extra = {'user_id': user_id}
        
        logger.info(f"Start {func.__name__}", extra={'extra': extra})
        start_time = time.time()
        
        try:
            result = await func(*args, **filtered_kwargs)
            exec_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {exec_time:.2f}s",
                      extra={'extra': {**extra, 'exec_time': exec_time}})
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True,
                       extra={'extra': extra})
            raise
    return wrapper

# Классы состояний
class CardPayStates(StatesGroup):
    successful_photo_gaid = State()
    successful_photo_kurs = State()

class UserSelectionStates(StatesGroup):
    waiting_for_selection = State()
    selected_gaid = State()
    selected_kurs = State()

# Базовый класс для обработки данных
class OutputDataHandler:
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.data_file = f"{data_type}_data.json"
        
    def transliterate_filename(self, filename):
        """Транслитерирует имя файла с русского на английский."""
        try:
            return transliterate.translit(filename, 'ru', reversed=True)
        except transliterate.exceptions.TranslitException:
            logger.warning(f"Не удалось выполнить транслитерацию '{filename}'")
            return filename
    
    def load_data(self):
        """Загружает данные из JSON файла."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Ошибка декодирования JSON из {self.data_file}")
                    return {}
        return {}
    
    def save_data(self, data):
        """Сохраняет данные в JSON файл."""
        with open(self.data_file, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    async def start(self, message: Message, bot: Bot):
        """Начало работы с данными."""
        check_func = getattr(rq, f'proverka_{self.data_type}s')
        if await check_func() is None:
            logger.warning(f"Нет доступных {self.data_type}ов")
            data_name = "гайд" if self.data_type == "gaid" else "курс"
            await bot.send_message(message.from_user.id, f'Пока {data_name}ов нет')
        else:
            keyboard_func = getattr(kb, f'selectkeyboard{self.data_type}')
            data_name = "гайд" if self.data_type == "gaid" else "курс"
            await bot.send_message(
                message.from_user.id,
                f'📖{data_name.capitalize()}ы: ' if self.data_type == 'gaid' else f'🤓{data_name.capitalize()}ы: ',
                reply_markup=await keyboard_func()
            )
    
    async def select(self, callback: CallbackQuery, state: FSMContext):
        """Обработка выбора конкретного элемента."""
        await callback.answer('')

        if not hasattr(callback, 'from_user') or not callback.from_user:
            logger.error("Нет данных пользователя в callback")
            return

        user_name = callback.from_user.full_name
        admin_id = os.getenv('ADMIN_ID')
        selection_id = callback.data.split('_')[1] 
        
        # Сохранение выбранного элемента в состояние
        await state.update_data(
            selection_id=selection_id,
            user_id=callback.from_user.id,
            user_name=user_name,
            admin_id=admin_id,
            data_type=self.data_type
        )

        if self.data_type == 'gaid':
            await state.set_state(UserSelectionStates.selected_gaid)
        else:
            await state.set_state(UserSelectionStates.selected_kurs)
        
        # Сохранение в JSON
        data = self.load_data()
        if str(user_name) not in data:
            data[str(user_name)] = []
        
        get_func = getattr(rq, f'get_{self.data_type}')
        items = await get_func(selection_id)
        if not items:
            await logger.error("Элемент не найден в базе данных")
            return
        
        for item in items:
            transliterated_name = self.transliterate_filename(
                item.name_fail_gaid if self.data_type == 'gaid' else item.name_fail_kurs
            )
            
            if transliterated_name not in data[str(user_name)]:
                data[str(user_name)].append(transliterated_name)
        
        self.save_data(data)
        
        # Отправка информации о выбранном элементе
        for item in items:
            photo_field = getattr(item, f'photo_{self.data_type}')
            name_field = getattr(item, f'name_fail_{self.data_type}')
            description_field = getattr(item, f'description_{self.data_type}')
            price_card_field = getattr(item, f'price_card_{self.data_type}')
            price_star_field = getattr(item, f'price_star_{self.data_type}')
            
            await callback.message.answer_photo(photo_field)
            await callback.message.answer(
                f'{html.bold("Гайд:" if self.data_type == "gaid" else "Курс:")} {name_field}\n'
                f'{html.bold("Описание:")} {description_field}\n'
                f'{html.bold("Стоимость в рублях:")} {price_card_field}\n'
                f'{html.bold("Стоимость в звездах:")} {price_star_field}',
                reply_markup=getattr(kb, f'payment_keyboard_{self.data_type}')
            )
    
    async def buy_with_stars(self, callback: CallbackQuery, state: FSMContext):
        """Покупка с использованием звезд."""
        data = await state.get_data()
        selection_id = data.get('selection_id')
        
        if not selection_id:
            await logger.error("Ошибка: не выбран элемент")
            return
            
        get_func = getattr(rq, f'get_{self.data_type}')
        items = await get_func(selection_id)
        
        for item in items:
            name_field = getattr(item, f'name_fail_{self.data_type}')
            description_field = getattr(item, f'description_{self.data_type}')
            price_star_field = getattr(item, f'price_star_{self.data_type}')
            
            await callback.message.answer_invoice(
                title=name_field,
                description=description_field,
                provider_token='',
                currency="XTR",
                payload=self.data_type,
                prices=[LabeledPrice(label="XTR", amount=price_star_field)]
            )
        await callback.answer()
    
    async def successful_payment(self, message: Message, bot: Bot, state: FSMContext):
        """Обработка успешной оплаты."""
        data = await state.get_data()
        selection_id = data.get('selection_id')
        
        if not selection_id:
            await logger.error("Ошибка: не выбран элемент")
            return
            
        get_func = getattr(rq, f'get_{self.data_type}')
        items = await get_func(selection_id)
        
        for item in items:
            file_field = getattr(item, f'fail_{self.data_type}')
            await bot.send_document(
                chat_id=message.from_user.id,
                document=file_field,
                caption=f"{'Гайд' if self.data_type == 'gaid' else 'Курс'}: {getattr(item, f'name_fail_{self.data_type}')}"
            )

        await state.clear()    
        logger.info(f"Состояние очищено после успешной оплаты для пользователя {message.from_user.id}")

        try:
            await bot.refund_star_payment(
                message.from_user.id,
                message.successful_payment.telegram_payment_charge_id
            )
        except Exception as e:
            logger.error(f"Ошибка при возврате оплаты: {e}")
    
    async def pay_with_card(self, callback: CallbackQuery, state: FSMContext):
        """Обработка оплаты картой."""
        await callback.answer()
        
        # Сохраняем текущие данные перед изменением состояния
        await state.update_data(client_id=callback.from_user.id)
        
        load_dotenv()
        phone = os.getenv('PHONE')
        
        logger.info(f"Установка состояния для {self.data_type} оплата картой")
        
        if self.data_type == 'gaid':
            await state.set_state(CardPayStates.successful_photo_gaid)
        else:
            await state.set_state(CardPayStates.successful_photo_kurs)

        data_name = "гайд" if self.data_type == "gaid" else "курс"    
        
        await callback.message.answer(
            f'Переведите на этот номер телефона сумму указанную в описании {data_name}а {phone}'
        )
        await callback.message.answer(
            'Прикрепите чек🧾, для подтверждения оплаты!\n\n'
            'Если вы нажали не на ту кнопку, напишите "стоп"'
        )
    
    async def process_payment_photo(self, message: Message, state: FSMContext, bot: Bot):
        """Обработка фото чека об оплате."""
        logger.info(f"Обработка платежной фотографии для {self.data_type}")
        
        if message.text and message.text.lower() == "стоп":
            await state.clear()
            logger.info(f"Пользователь {message.from_user.id} отменил оплату")
            await message.answer("Процесс оплаты отменен.")
            return
            
        # if not message.photo:
        #     await message.answer('Прикрепите скриншот вашего чека по оплате пожалуйста')
        #     return
        
        # Получаем данные из состояния
        current_state = await state.get_state()
        data = await state.get_data()
        logger.info(f"Обработка платежной фотографии для {self.data_type}, состояние: {current_state}")
        logger.info(f"Данные состояния: {data}")
        user_id = data.get('user_id')
        selection_id = data.get('selection_id')
        admin_id = data.get('admin_id')
        
        logger.info(f"User ID: {user_id}, Selection ID: {selection_id}, Admin ID: {admin_id}")
        
        pay_photo_check = None

        # Сохраняем фото
        try:
            if message.document: 
                await message.answer("Пожалуйста, отправьте именно 📸 <b>скриншот</b> (как изображение), а не файл-документ.", parse_mode='HTML')
                logger.warn("Получен файл-документ, вернул пользователю сообщение о просьбе прислать фото")
                return
            elif message.photo:
                if message.photo[-1].file_size > 5 * 1024 * 1024:
                    await message.answer("Изображение слишком большое. Пожалуйста, сделайте скриншот меньше или обрежьте его.")
                    return
                else:
                    pay_photo_check = message.photo[-1].file_id
                    await state.update_data(pay_photo_check=pay_photo_check)
                    logger.info("Получено сжатое фото")
            else:
                await message.answer('Прикрепите скриншот вашего чека по оплате пожалуйста')
                return
        except (TypeError, IndexError):
            await message.answer('Прикрепите скриншот вашего чека по оплате пожалуйста')
            return
        
        await bot.send_message(chat_id=user_id, text='Ожидайте подтверждение вашей оплаты админом')
        
        # Если admin_id не найден в состоянии, получаем из .env
        if not admin_id:
            load_dotenv()
            admin_id = int(os.getenv('ADMIN_ID'))
        
        keyboard = getattr(kb, f'succsefull_keyboard_{self.data_type}')
        
        # Сохраняем необходимые данные для подтверждения
        await state.update_data(
            admin_message_data={
                'client_id': user_id,
                'selection_id': selection_id,
                'data_type': self.data_type,
                'photo': pay_photo_check,
                'admin_id': admin_id 
            }
        )
        
        chekmessage = await bot.send_photo(
            chat_id=admin_id,
            caption='Проверьте оплату на корректность:',
            photo=pay_photo_check,
            reply_markup=keyboard
        )
        
        # Сохраняем ID сообщения для админа
        await state.update_data(admin_message_id=chekmessage.message_id)
        
        logger.info(f"Фотография отправлена администратору {admin_id}")
        
        # Не очищаем состояние полностью, сохраняем необходимые данные
        if self.data_type == 'gaid':
            await state.set_state(CardPayStates.successful_photo_gaid)
        else:
            await state.set_state(CardPayStates.successful_photo_kurs)
        


# Создаем экземпляры обработчиков
gaid_handler = OutputDataHandler('gaid')
kurs_handler = OutputDataHandler('kurs')

# Регистрация обработчиков для гайдов
@router.message(Command(commands='gaid'))
@log_user_action
async def gaid_start(message: Message, bot: Bot):
    await gaid_handler.start(message, bot)

@router.callback_query(F.data.startswith('selectgaid_'))
@log_user_action
async def gaid_select(callback: CallbackQuery, state: FSMContext):
    await gaid_handler.select(callback, state)

@router.callback_query(F.data.startswith('stars_gaid'))
@log_user_action
async def buy_gaid(callback: CallbackQuery, state: FSMContext):
    await gaid_handler.buy_with_stars(callback, state)

@router.pre_checkout_query()
async def pre_checkout_query_gaid(event: PreCheckoutQuery) -> None:
    await event.answer(ok=True)

@router.message(F.successful_payment.invoice_payload == 'gaid')
@log_user_action
async def successful_payment_gaid(message: Message, bot: Bot, state: FSMContext):
    await gaid_handler.successful_payment(message, bot, state)

@router.callback_query(F.data.startswith('cards_gaid'))
@log_user_action
async def pay_photo_check_get_gaid(callback: CallbackQuery, state: FSMContext):
    await gaid_handler.pay_with_card(callback, state)

@router.message(CardPayStates.successful_photo_gaid)
@log_user_action
async def successful_photo_gaid(message: Message, state: FSMContext, bot: Bot):
    await gaid_handler.process_payment_photo(message, state, bot)

# Регистрация обработчиков для курсов
@router.message(Command(commands='kurs'))
@log_user_action
async def kurs_start(message: Message, bot: Bot):
    await kurs_handler.start(message, bot)

@router.callback_query(F.data.startswith('selectkurs_'))
@log_user_action
async def kurs_select(callback: CallbackQuery, state: FSMContext):
    await kurs_handler.select(callback, state)

@router.callback_query(F.data.startswith('stars_kurs'))
@log_user_action
async def buy_kurs(callback: CallbackQuery, state: FSMContext):
    await kurs_handler.buy_with_stars(callback, state)

@router.message(F.successful_payment.invoice_payload == 'kurs')
@log_user_action
async def successful_payment_kurs(message: Message, bot: Bot, state: FSMContext):
    await kurs_handler.successful_payment(message, bot, state)

@router.callback_query(F.data.startswith('cards_kurs'))
@log_user_action
async def pay_photo_check_get_kurs(callback: CallbackQuery, state: FSMContext):
    await kurs_handler.pay_with_card(callback, state)

@router.message(CardPayStates.successful_photo_kurs)
@log_user_action
async def successful_photo_kurs(message: Message, state: FSMContext, bot: Bot):
    await kurs_handler.process_payment_photo(message, state, bot)

# Обработчики подтверждения оплаты (остаются без изменений)
@router.callback_query(F.data.startswith('true_gaid'))
@log_user_action
async def Trueanswer(callback: CallbackQuery):
    await callback.answer()
    chekkeyboard = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_gaid)
    await asyncio.sleep(900)
    await chekkeyboard.delete()

@router.callback_query(F.data.startswith('false_gaid'))
@log_user_action
async def Falseanswer(callback: CallbackQuery):
    await callback.answer()
    chekkeyboard = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_false_gaid)
    await asyncio.sleep(900)
    await chekkeyboard.delete()

@router.callback_query(F.data.startswith('yes_false_gaid'))
@log_user_action
async def Confirmanswer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    client_id = admin_data.get('client_id')
    await callback.answer()
    await state.clear()
    logger.info(f"Состояние очищено перед сообщением пользователю о неккоректности платежа  для {client_id}")
    falsecheck = await callback.message.answer('Понял вас! Сообщаю о неккоректности платежа пользователю!')
    await bot.send_message(chat_id=client_id, text='Админ не подтвердил ваш платеж! Перепроверьте оплату!')
    await asyncio.sleep(900)
    await falsecheck.delete()


@router.callback_query(F.data.startswith('no_false_gaid'))
@log_user_action
async def UnConfirmanswer(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    admin = admin_data.get('admin_id')
    photo = admin_data.get('photo')

    if not admin or not photo:
        load_dotenv()
        admin = int(os.getenv('ADMIN_ID'))
        if not photo:
            photo = data.get('pay_photo_check')

    await callback.answer()
    chekmessage = await bot.send_photo(chat_id=admin, caption='Проверьте оплату на корректность:', photo=photo, reply_markup=kb.succsefull_keyboard_gaid)
    await asyncio.sleep(900)
    await chekmessage.delete()

@router.callback_query(F.data.startswith('ok_gaid'))
@log_user_action
async def ConfirmanswerYes(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    client_id = admin_data.get('client_id')
    selection_id = admin_data.get('selection_id')
    
    if not client_id or not selection_id:
        await callback.answer("Данные не найдены")
        return
        
    await state.clear()
    logger.info(f"Состояние очищено перед отправкой гайда для {client_id}")

    gaidsel = await rq.get_gaid(selection_id)
    await callback.answer()
    try:
        sendmessageg = await callback.message.answer('Отправляю гайд счастливчику🥳')
        for gaid in gaidsel:
            await bot.send_document(
                chat_id=client_id,
                document=gaid.fail_gaid,
                caption=f"Гайд: {gaid.name_fail_gaid}"
            )
        logger.info(f"Гайд доставлен {client_id}")
    except TelegramBadRequest as e:
        await callback.message.answer('Гайд не отправился...\nОшибка уже отправлена Тех.Админу! Не переживайте, работы уже ведутся!')
        await bot.send_message(chat_id=client_id, text="Не удалось отправить вам гайд. Мы работаем уже над этой проблемой. Обязательно вам пришлем гайд, как решим данную ошибку. Приносим свои извинения, за предоставленные неудобства!")
        logger.error(f'Не удалось отправить гайд: {e}')
    await asyncio.sleep(900)
    await sendmessageg.delete()


@router.callback_query(F.data.startswith('no_gaid'))
@log_user_action
async def UnConfirmanswerno(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    admin = admin_data.get('admin_id')
    photo = admin_data.get('photo')

    if not admin or not photo:
        load_dotenv()
        admin = int(os.getenv('ADMIN_ID'))
        if not photo:
            photo = data.get('pay_photo_check')

    await callback.answer()
    chekmessage = await bot.send_photo(chat_id=admin, caption='Проверьте оплату на корректность:', photo=photo, reply_markup=kb.succsefull_keyboard_gaid)
    await asyncio.sleep(900)
    await chekmessage.delete()


@router.callback_query(F.data.startswith('true_kurs'))
@log_user_action
async def Trueanswerkurs(callback: CallbackQuery):
    await callback.answer()
    chekkeyboardtrue = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_kurs)
    await asyncio.sleep(900)
    await chekkeyboardtrue.delete()


@router.callback_query(F.data.startswith('ok_kurs'))
@log_user_action
async def ConfirmanswerYeskurs(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    client_id = admin_data.get('client_id')
    selection_id = admin_data.get('selection_id')
    
    if not client_id or not selection_id:
        await callback.answer("Данные не найдены")
        return
    
    await callback.answer()
    await state.clear()
    logger.info(f"Состояние очищено перед отправкой курса для {client_id}")
    kurssel = await rq.get_kurs(selection_id)
    try:
        sendmessagek = await callback.message.answer('Отправляю курс счастливчику🥳')
        for kurs in kurssel:
            await bot.send_document(
                chat_id=client_id,
                document=kurs.fail_kurs,
                caption=f"Курс: {kurs.name_fail_kurs}"
            )
        logger.info(f"Курс доставлен {client_id}")
    except TelegramBadRequest as e:
        sendmessageerror = await callback.message.answer('Курс не отправился...\nОшибка уже отправлена Тех.Админу! Не переживайте, работы уже ведутся!')
        await bot.send_message(chat_id=client_id, text="Не удалось отправить вам курс. Мы работаем уже над этой проблемой. Обязательно вам пришлем курс, как решим данную ошибку. Приносим свои извинения, за предоставленные неудобства!")
        print(f'Не удалось отправить курс: {e} -> Походу опять file_id устарел...\nАйди клиента:{client_id}\nНазвание товара:{kurs.name_fail_kurs}\nЕго товар:{kurs.fail_kurs}')
    await asyncio.sleep(900)
    await sendmessagek.delete()
    await sendmessageerror.delete()
    await state.clear()

@router.callback_query(F.data.startswith('false_kurs'))
@log_user_action
async def Falseanswerkurs(callback: CallbackQuery):
    await callback.answer()
    chekkeyboardfalse = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_false_kurs)
    await asyncio.sleep(900)
    await chekkeyboardfalse.delete()

@router.callback_query(F.data.startswith('yes_false_kurs'))
@log_user_action
async def Confirmanswerkurs(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    client_id = admin_data.get('client_id')
    await callback.answer()
    await state.clear()
    logger.info(f"Состояние очищено перед сообщением пользователю о неккоректности платежа  для {client_id}")
    falsecheckyesfalse = await callback.message.answer('Понял вас! Сообщаю о неккоректности платежа пользователю!')
    await bot.send_message(chat_id=client_id, text='Админ не подтвердил ваш платеж! Перепроверьте оплату!')
    await asyncio.sleep(900)
    await falsecheckyesfalse.delete()


@router.callback_query(F.data.startswith('no_false_kurs'))
@log_user_action
async def UnConfirmanswerkurs(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    admin = admin_data.get('admin_id')
    photo = admin_data.get('photo')

    if not admin or not photo:
        load_dotenv()
        admin = int(os.getenv('ADMIN_ID'))
        if not photo:
            photo = data.get('pay_photo_check')

    await callback.answer()
    chekmessagenofalse = await bot.send_photo(chat_id=admin, caption='Проверьте оплату на корректность:', photo=photo, reply_markup=kb.succsefull_keyboard_kurs)
    await asyncio.sleep(900)
    await chekmessagenofalse.delete()


@router.callback_query(F.data.startswith('no_kurs'))
@log_user_action
async def UnConfirmanswernokurs(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    admin_data = data.get('admin_message_data', {})
    admin = admin_data.get('admin_id')
    photo = admin_data.get('photo')

    if not admin or not photo:
        load_dotenv()
        admin = int(os.getenv('ADMIN_ID'))
        if not photo:
            photo = data.get('pay_photo_check')

    await callback.answer()
    chekmessage = await bot.send_photo(chat_id=admin, caption='Проверьте оплату на корректность:', photo=photo, reply_markup=kb.succsefull_keyboard_kurs)
    await asyncio.sleep(900)
    await chekmessage.delete()

@router.message()
@log_user_action
async def log_all_messages(message: Message):
    logger.debug(f"Необработанное сообщение: {message.text}")


@router.message(Command(commands=['gaid', 'kurs']))
async def cancel_any_state(message: Message, state: FSMContext):
    """Сбрасывает любое состояние при получении основных команд"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        logger.info(f"Состояние сброшено для пользователя {message.from_user.id} при команде {message.text}")
    if message.text == '/gaid':
        await gaid_start(message, Bot.get_current())
    elif message.text == '/kurs':
        await kurs_start(message, Bot.get_current())
