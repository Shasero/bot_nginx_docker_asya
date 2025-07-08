from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import database.requests as rq

router = Router()


class AddKurs(StatesGroup):
    nameurl = State()
    descriptionkurs = State()
    url = State()
    pricecardkurs = State()
    pricestarkurs = State()


@router.callback_query(F.data.startswith('keyboardaddkurs'))
async def addpoleurl(callback: CallbackQuery, state: FSMContext, bot: Bot):
    chat_id = callback.from_user.id
    last_message_id = callback.message.message_id
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
    await state.set_state(AddKurs.nameurl)
    await callback.message.answer( 'Введите название курса: ')


@router.message(AddKurs.nameurl)
async def addnameurl(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(nameurl=message.text)
    await state.set_state(AddKurs.descriptionkurs)
    await bot.send_message(message.from_user.id,'Введите описание: ')


@router.message(AddKurs.descriptionkurs)
async def adddescriptionkurs(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(descriptionkurs=message.text)
    await state.set_state(AddKurs.url)
    await bot.send_message(message.from_user.id,'Вставте ссылку на курс: ')


@router.message(AddKurs.url)
async def addurl(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(url=message.text)
    await state.set_state(AddKurs.pricecardkurs)
    await bot.send_message(message.from_user.id,'Укажите цену курса в рублях: ')


@router.message(AddKurs.pricecardkurs)
async def addpricecardkurs(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(pricecardkurs=message.text)
    await state.set_state(AddKurs.pricestarkurs)
    await bot.send_message(message.from_user.id,'Укажите цену курса в звездах: ')


@router.message(AddKurs.pricestarkurs)
async def addpricestarkurs(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(pricestarkurs=message.text)
    addata = await state.get_data()
    nameurl = addata.get('nameurl')
    descriptionkurs = addata.get('descriptionkurs')
    url = addata.get('url')
    pricecardkurs = addata.get('pricecardkurs')
    pricestarkurs = addata.get('pricestarkurs')
    await rq.addkurs(nameurl, descriptionkurs, url, pricecardkurs, pricestarkurs)
    await bot.send_message(message.from_user.id,'Данные добавлены успешно!')
    await state.clear()