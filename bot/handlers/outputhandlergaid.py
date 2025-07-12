from aiogram import F, Router, html, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
import asyncio
import time
import json
import os
import transliterate
import os


import keyboards.keyboard as kb
import database.requests as rq


router = Router()
gaid_selections = {}
kurs_selections = {}
getgaid = None



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
async def gaid_start(message: Message, bot: Bot):
    if(await rq.proverka_gaids() == None):
        await bot.send_message(message.from_user.id,'Пока гайдов нет')
    else:
        await bot.send_message(message.from_user.id,'📖Гайды: ',reply_markup=await kb.selectkeyboardgaid())


@router.callback_query(F.data.startswith('selectgaid_'))
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
    await callback.message.photo(f'{gaid.photo}')
    await callback.message.answer(f'{html.bold('Гайд:')} {gaid.namefail}\n{html.bold('Описание:')} {gaid.descriptiongaid}\n{html.bold('Стоимость в рублях:')} {gaid.pricecardgaid}\n{html.bold('Стоимость в звездах:')} {gaid.pricestargaid}', reply_markup=kb.payment_keyboard_gaid)


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
    if message.text != "стоп":
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
async def ConfirmanswerYes(callback: CallbackQuery, bot: Bot):
    gaidsel = await rq.get_gaid(getgaid)
    await callback.answer()
    try:
        sendmessageg = await callback.message.answer('Отправляю гайд счастливчику🥳')
        for gaid in gaidsel:
            await bot.send_document(chat_id=clientidgaid, document=gaid.fail)
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