from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

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
    chat_id = callback.from_user.id
    last_message_id = callback.message.message_id
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
    await state.set_state(AddGaid.namefail)
    await callback.message.answer('Введите название файла: ')


@router.message(AddGaid.namefail)
async def addnamefail(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(namefail=message.text)
    await state.set_state(AddGaid.descriptiongaid)
    await bot.send_message(message.from_user.id,'Введите описание: ')


@router.message(AddGaid.descriptiongaid)
async def adddescriptiongaid(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(descriptiongaid=message.text)
    await state.set_state(AddGaid.fail)
    await bot.send_message(message.from_user.id,'Зарузите файл: ')


@router.message(AddGaid.fail)
async def addfail(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(fail=message.document.file_id)
    await state.set_state(AddGaid.pricecardgaid)
    await bot.send_message(message.from_user.id,'Укажите цену гайда в рублях: ')


@router.message(AddGaid.pricecardgaid)
async def addpricecardgaid(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(pricecardgaid=message.text)
    await state.set_state(AddGaid.pricestargaid)
    await bot.send_message(message.from_user.id,'Укажите цену гайда в звездах: ')

@router.message(AddGaid.pricestargaid)
async def addpricestargaid(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(pricestargaid=message.text)
    addata = await state.get_data()
    namefail = addata.get('namefail')
    descriptiongaid = addata.get('descriptiongaid')
    fail = addata.get('fail')
    pricecardgaid = addata.get('pricecardgaid')
    pricestargaid = addata.get('pricestargaid')
    await rq.addgaid(namefail, descriptiongaid, fail, pricecardgaid, pricestargaid)
    await bot.send_message(message.from_user.id,'Данные добавлены успешно!')
    await state.clear()