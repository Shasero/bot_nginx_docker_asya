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
kurs_selections = {}
selectkurs = None


DATA_FILE_KURS = "kurs_data.json"


def load_data_kurs():
    if os.path.exists(DATA_FILE_KURS):
        with open(DATA_FILE_KURS, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Ошибка при декодировании JSON из {DATA_FILE_KURS}. Начиная с пустых данных.")
                return {}
    else:
        return {}
    

def save_data_kurs(data_kurs):
    with open(DATA_FILE_KURS, "w") as f:
        json.dump(data_kurs, f, indent=4)

    
def transliterate_filename(filename):
    "Транслитерирует имя файла с русского на английский."
    try:
        return transliterate.translit(filename, 'ru', reversed=True)
    except transliterate.exceptions.TranslitException:
        print(f"Предупреждение: Не удалось выполнить транслитерацию '{filename}', используя оригинальное имя.")
        return filename


@router.message(Command(commands='kurs'))
async def kurs_start(message: Message, bot: Bot):
    if(await rq.proverka_kurss() == None):
        await bot.send_message(message.from_user.id,'Пока курсов нет')
    else:
        await bot.send_message(message.from_user.id,'🤓Курсы: ',reply_markup=await kb.selectkeyboardkurs())


@router.callback_query(F.data.startswith('selectkurs_'))
async def kursselect(callback: CallbackQuery):
    start_time = time.time()
    end_time = start_time + 15 * 60
    await callback.answer('')
    k = []
    user_name = callback.from_user.full_name
    selectk = callback.data.split('_')[1]
    global selectkurs
    selectkurs = selectk
    # Загружать данные из JSON

    data_kurs = load_data_kurs()

    # Добавьте выбранное руководство в список пользователя в данных JSON
    if str(user_name) not in data_kurs:
        data_kurs[str(user_name)] = []
    
    #получение дополнительной информации из базы данных
    kurssel = await rq.get_kurs(selectkurs)
    
    for kurs in kurssel:
        #Ошибка транслитерации имени из базы данных
        transliterated_filename = transliterate_filename(kurs.nameurl)

        if transliterated_filename not in data_kurs[str(user_name)]:
          data_kurs[str(user_name)].append(transliterated_filename)

    # Сохранение обновленных данных в формате JSON
    save_data_kurs(data_kurs)

    while start_time < end_time:
        
        if user_name not in kurs_selections:
            kurs_selections[user_name] = []

        if selectk not in kurs_selections[user_name]:
            kurs_selections[user_name].append(selectk)
        k.append(kurs_selections)
        break

    await callback.message.answer(f'{html.bold('Курс:')} {kurs.nameurl}\n{html.bold('Описание:')} {kurs.descriptionkurs}\n{html.bold('Стоимость в рублях:')} {kurs.pricecardkurs}\n{html.bold('Стоимость в звездах:')} {kurs.pricestarkurs}', reply_markup=kb.payment_keyboard_kurs)


@router.callback_query(F.data.startswith('stars_kurs'))
async def buykurs(callback: CallbackQuery):
    kurssel = await rq.get_kurs(selectkurs)
    for kurs in kurssel:
        nameurl = kurs.nameurl
        descriptionkurs = kurs.descriptionkurs
        pricestar = kurs.pricestarkurs

    await callback.message.answer_invoice(
            title=nameurl,
            description=descriptionkurs,
            provider_token='',
            currency="XTR",
            payload='kurs',
            prices=[LabeledPrice(label="XTR", amount=pricestar)]
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_querykurs(event: PreCheckoutQuery) -> None:
    await event.answer(ok=True)


@router.message(F.successful_payment.invoice_payload == 'kurs')
async def successful_paymentkurs(message: Message, bot: Bot) -> None:
    kurssel = await rq.get_kurs(selectkurs)
    for kurs in kurssel:
        await message.answer(kurs.url)
    await bot.refund_star_payment(message.from_user.id, message.successful_payment.telegram_payment_charge_id)


load_dotenv()

admin_id = os.getenv('ADMIN_ID')
intadmin_id = int(admin_id)
phone = os.getenv('PHONE')


class Card_Pay_kurs(StatesGroup):
    successful_photo_kurs = State()
photo_kurs = None
clientidkurs = None


@router.callback_query(F.data.startswith('cards_kurs'))
async def payphotocheckgetkurs(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    global clientidkurs
    infopokup = callback.from_user.id
    clientidkurs = infopokup
    if callback.message.text != "стоп":
        await state.set_state(Card_Pay_kurs.successful_photo_kurs)
        await callback.message.answer(f'Переведите на этот номер телефона сумму указанную в описании гайда {phone}')
        await callback.message.answer('Прекрипите чек🧾, для подтверждения оплаты!\n\nЕсли вы нажали не на ту кнопку, напишите "стоп"')
    else:
        await state.clear()


@router.message(Card_Pay_kurs.successful_photo_kurs)
async def successfulphotokurs(message: Message, state: FSMContext, bot: Bot):
    if message.text != "стоп":
        await state.update_data(pay_photo_checkurs=message.photo[-1].file_id)
        await bot.send_message(chat_id=clientidkurs, text='Ожидайте подтверждение вашей оплаты админом')
        data = await state.get_data()
        global photo_kurs
        pay_photo_checkurs = data.get('pay_photo_checkurs')
        photo_kurs = pay_photo_checkurs
        chekmessage = await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=photo_kurs, reply_markup=kb.succsefull_keyboard_kurs)
        await state.clear()
        await asyncio.sleep(900)
        await chekmessage.delete()
    else: 
        await state.clear()


@router.callback_query(F.data.startswith('true_kurs'))
async def Trueanswerkurs(callback: CallbackQuery):
    await callback.answer()
    chekkeyboardtrue = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_kurs)
    await asyncio.sleep(900)
    await chekkeyboardtrue.delete()


@router.callback_query(F.data.startswith('ok_kurs'))
async def ConfirmanswerYeskurs(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    kurssel = await rq.get_kurs(selectkurs)
    try:
        sendmessagek = await callback.message.answer('Отправляю курс счастливчику🥳')
        for kurs in kurssel:
            await bot.send_message(chat_id=clientidkurs, text=kurs.url)
    except TelegramBadRequest as e:
        sendmessageerror = await callback.message.answer('Курс не отправился...\nОшибка уже отправлена Тех.Админу! Не переживайте, работы уже ведутся!')
        await bot.send_message(chat_id=clientidkurs, text="Не удалось отправить вам курс. Мы работаем уже над этой проблемой. Обязательно вам пришлем курс, как решим данную ошибку. Приносим свои извинения, за предоставленные неудобства!")
        print(f'Не удалось отправить курс: {e} -> Походу опять file_id устарел...\nАйди клиента:{clientidkurs}\nНазвание товара:{kurs.nameurl}\nЕго товар:{kurs.url}')
        # sendurl = await callback.message.answer(chat_id=clientid, text=kurs.url)
    await asyncio.sleep(900)
    await sendmessagek.delete()
    await sendmessageerror.delete()

@router.callback_query(F.data.startswith('false_kurs'))
async def Falseanswerkurs(callback: CallbackQuery):
    await callback.answer()
    chekkeyboardfalse = await callback.message.answer('Вы точно все внимательно проверили?', reply_markup=kb.confirmation_false_kurs)
    await asyncio.sleep(900)
    await chekkeyboardfalse.delete()

@router.callback_query(F.data.startswith('yes_false_kurs'))
async def Confirmanswerkurs(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    falsecheckyesfalse = await callback.message.answer('Понял вас! Сообщаю о неккоректности платежа пользователю!')
    await bot.send_message(chat_id=clientidkurs, text='Админ не подтвердил ваш платеж! Перепроверьте оплату!')
    await asyncio.sleep(900)
    await falsecheckyesfalse.delete()


@router.callback_query(F.data.startswith('no_false_kurs'))
async def UnConfirmanswerkurs(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    chekmessagenofalse = await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=photo_kurs, reply_markup=kb.succsefull_keyboard_kurs)
    await asyncio.sleep(900)
    await chekmessagenofalse.delete()


@router.callback_query(F.data.startswith('no_kurs'))
async def UnConfirmanswernokurs(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    chekmessage = await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=photo_kurs, reply_markup=kb.succsefull_keyboard_kurs)
    await asyncio.sleep(900)
    await chekmessage.delete()