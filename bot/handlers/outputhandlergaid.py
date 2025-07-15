import logging 
from logging.handlers import RotatingFileHandler
import json
from aiogram import F, Router, html, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import asyncio
import time
import os
import transliterate
from datetime import datetime


import keyboards.keyboard as kb
import database.requests as rq


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
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
    
    # Ротация логов (10 MB, 3 файла)
    file_handler = RotatingFileHandler(
        'logs/gaid_handler.log',
        maxBytes=10*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(JsonFormatter())
    
    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()


router = Router()
gaid_selections = {}
kurs_selections = {}
getgaid = None


def log_user_action(func):
    """Декоратор для логирования действий пользователя"""
    async def wrapper(*args, **kwargs):
        message_or_callback = args[0]
        user_id = getattr(message_or_callback.from_user, 'id', None)
        extra = {'user_id': user_id}
        
        logger.info(
            f"Start {func.__name__}",
            extra={'extra': extra}
        )
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            exec_time = time.time() - start_time
            logger.info(
                f"Completed {func.__name__} in {exec_time:.2f}s",
                extra={'extra': {**extra, 'exec_time': exec_time}}
            )
            return result
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True,
                extra={'extra': extra}
            )
            raise
    return wrapper



# Определите путь к файлу JSON
DATA_FILE_GAID = "gaid_data.json"

# Загрузите существующие данные из файла JSON (если он существует).
def load_data_gaid():
    if os.path.exists(DATA_FILE_GAID):
        with open(DATA_FILE_GAID, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Ошибка при декодировании JSON из {DATA_FILE_GAID}. Начиная с пустых данных.")
                return {}
    else:
        return {}

# Сохраните данные в JSON-файл
def save_data_gaid(data_gaid):
    with open(DATA_FILE_GAID, "w") as f:
        json.dump(data_gaid, f, indent=4)


def transliterate_filename(filename):
    "Транслитерирует имя файла с русского на английский."
    try:
        return transliterate.translit(filename, 'ru', reversed=True)
    except transliterate.exceptions.TranslitException:
        print(f"Предупреждение: Не удалось выполнить транслитерацию '{filename}', используя оригинальное имя.")
        return filename

@router.message(Command(commands='gaid'))
@log_user_action
async def gaid_start(message: Message, bot: Bot):
    if(await rq.proverka_gaids() == None):
        logger.warning("Нет доступных гайдов")
        await bot.send_message(message.from_user.id,'Пока гайдов нет')
    else:
        logger.debug("Отправка клавиатуры с гайдами")
        await bot.send_message(message.from_user.id,'📖Гайды: ',reply_markup=await kb.selectkeyboardgaid())


@router.callback_query(F.data.startswith('selectgaid_'))
@log_user_action
async def gaidselect(callback: CallbackQuery):
    start_time = time.time()
    end_time = start_time + 15 * 60
    await callback.answer('')
    p = []
    user_name = callback.from_user.full_name
    getgaidselect = callback.data.split('_')[1]
    global getgaid
    getgaid = getgaidselect
    # selectintgaid = int(select)

    data_gaid = load_data_gaid()

    if str(user_name) not in data_gaid:
        data_gaid[str(user_name)] = []
    
    gaidsel = await rq.get_gaid(getgaid)
    logger.debug(f"Retrieved guide data: {getgaid}")
    
    for gaid in gaidsel:
        transliterated_filename = transliterate_filename(gaid.namefail)

        if transliterated_filename not in data_gaid[str(user_name)]:
          data_gaid[str(user_name)].append(transliterated_filename)

    save_data_gaid(data_gaid)

    while start_time < end_time:
        
        if user_name not in gaid_selections:
            gaid_selections[user_name] = []

        if getgaidselect not in gaid_selections[user_name]:
            gaid_selections[user_name].append(getgaidselect)
        p.append(gaid_selections)
        break

    await callback.message.answer_photo(f'{gaid.photo}')
    await callback.message.answer(
        f'{html.bold("Гайд:")} {gaid.namefail}\n'
        f'{html.bold("Описание:")} {gaid.descriptiongaid}\n'
        f'{html.bold("Стоимость в рублях:")} {gaid.pricecardgaid}\n'
        f'{html.bold("Стоимость в звездах:")} {gaid.pricestargaid}', 
        reply_markup=kb.payment_keyboard_gaid
    )


@router.callback_query(F.data.startswith('stars_gaid'))
async def buygaid(callback: CallbackQuery):
    gaidsel = await rq.get_gaid(getgaid)
    for gaid in gaidsel:
        namefail = gaid.namefail
        descriptiongaid = gaid.descriptiongaid
        pricestar = gaid.pricestargaid

    await callback.message.answer_invoice(
            title=namefail,
            description=descriptiongaid,
            provider_token='',
            currency="XTR",
            payload='gaids',
            prices=[LabeledPrice(label="XTR", amount=pricestar)]
    )
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout_querygaid(event: PreCheckoutQuery) -> None:
    await event.answer(ok=True)


@router.message(F.successful_payment.invoice_payload == 'gaids')
async def successful_paymentgaid(message: Message, bot: Bot) -> None:
    gaidsel = await rq.get_gaid(getgaid)
    for gaid in gaidsel:
        await message.answer_document(gaid.fail)
    await bot.refund_star_payment(message.from_user.id, message.successful_payment.telegram_payment_charge_id)


load_dotenv()

admin_id = os.getenv('ADMIN_ID')
intadmin_id = int(admin_id)
phone = os.getenv('PHONE')


class Card_Pay_gaid(StatesGroup):
    successful_photo_gaid = State()
photog = None
clientidgaid = None


@router.callback_query(F.data.startswith('cards_gaid'))
async def payphotocheckget(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    global clientidgaid
    infopokup = callback.from_user.id
    clientidgaid = infopokup
    if callback.message.text != "стоп":
        await state.set_state(Card_Pay_gaid.successful_photo_gaid)
        await callback.message.answer(f'Переведите на этот номер телефона сумму указанную в описании гайда {phone}')
        await callback.message.answer('Прекрипите чек🧾, для подтверждения оплаты!\n\nЕсли вы нажали не на ту кнопку, напишите "стоп"')
    else:
        await state.clear()


@router.message(Card_Pay_gaid.successful_photo_gaid)
async def successfulphoto(message: Message, state: FSMContext, bot: Bot):
    try:
        if message.text != "стоп":
            if not message.photo:
                await message.answer('Прекрипите скриншот вашего чека по оплате пожалуйста')
                return
            else:
                await state.update_data(payphotocheck=message.photo[-1].file_id)
                await bot.send_message(chat_id=clientidgaid, text='Ожидайте подтверждение вашей оплаты админом')
                data = await state.get_data()
                global photog
                payphotocheck = data.get('payphotocheck')
                photog = payphotocheck
                chekmessage = await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=payphotocheck, reply_markup=kb.succsefull_keyboard_gaid)
                await state.clear()
                await asyncio.sleep(900)
                await chekmessage.delete()
        else:
            await state.clear()
    except Exception as e:
        logging.error(f"Error in successfulphoto: {e}", exc_info=True)
        await message.answer("Ошибка при обработке фото. Попробуйте ещё раз.")


@router.callback_query(F.data.startswith('true_gaid'))
async def Trueanswer(callback: CallbackQuery):
    await callback.answer()
    chekkeyboard = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_gaid)
    await asyncio.sleep(900)
    await chekkeyboard.delete()

@router.callback_query(F.data.startswith('false_gaid'))
async def Falseanswer(callback: CallbackQuery):
    await callback.answer()
    chekkeyboard = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_false_gaid)
    await asyncio.sleep(900)
    await chekkeyboard.delete()

@router.callback_query(F.data.startswith('yes_false_gaid'))
async def Confirmanswer(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    falsecheck = await callback.message.answer('Понял вас! Сообщаю о неккоректности платежа пользователю!')
    await bot.send_message(chat_id=clientidgaid, text='Админ не подтвердил ваш платеж! Перепроверьте оплату!')
    await asyncio.sleep(900)
    await falsecheck.delete()


@router.callback_query(F.data.startswith('no_false_gaid'))
async def UnConfirmanswer(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    chekmessage = await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=photog, reply_markup=kb.succsefull_keyboard_gaid)
    await asyncio.sleep(900)
    await chekmessage.delete()

@router.callback_query(F.data.startswith('ok_gaid'))
@log_user_action
async def ConfirmanswerYes(callback: CallbackQuery, bot: Bot):
    gaidsel = await rq.get_gaid(getgaid)
    await callback.answer()
    try:
        sendmessageg = await callback.message.answer('Отправляю гайд счастливчику🥳')
        for gaid in gaidsel:
            await bot.send_document(
                chat_id=clientidgaid,
                document=gaid.fail,
                caption=f"Гайд: {gaid.namefail}"
            )
        logger.info(f"Гайд доставлен {clientidgaid}")
    except TelegramBadRequest as e:
        await callback.message.answer('Гайд не отправился...\nОшибка уже отправлена Тех.Админу! Не переживайте, работы уже ведутся!')
        await bot.send_message(chat_id=clientidgaid, text="Не удалось отправить вам гайд. Мы работаем уже над этой проблемой. Обязательно вам пришлем гайд, как решим данную ошибку. Приносим свои извинения, за предоставленные неудобства!")
        print(f'Не удалось отправить гайд: {e} -> Походу опять file_id устарел...\nАйди клиента:{clientidgaid}\nНазвание товара:{gaid.namefail}\nЕго товар:{gaid.fail}')
    await asyncio.sleep(900)
    await sendmessageg.delete()


@router.callback_query(F.data.startswith('no_gaid'))
async def UnConfirmanswerno(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    chekmessage = await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=photog, reply_markup=kb.succsefull_keyboard_gaid)
    await asyncio.sleep(900)
    await chekmessage.delete()