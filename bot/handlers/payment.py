# from aiogram import Router, html, Bot, F
# from aiogram.types import Message, CallbackQuery
# from aiogram.fsm.state import StatesGroup, State
# from aiogram.fsm.context import FSMContext

# from keyboards import keyboard as kb
# import database.requests as rq
# from handlers.outputhandle
# from dotenv import load_dotenv
# import os


# router = Router()

# load_dotenv()

# admin_id = os.getenv('ADMIN_ID')
# intadmin_id = int(admin_id)


# class CardPay(StatesGroup):
#     successfulphoto = State()


# @router.callback_query(F.data.startswith('paycardsgaid'))
# async def payphotocheckget(callback: CallbackQuery, state: FSMContext, message: Message):
#     await callback.answer()
#     await state.set_state(CardPay.successfulphoto)
#     global clientid
#     infopokup = message.from_user.id
#     clientid = infopokup
#     await callback.message.answer('Прекрипите чек, для подтверждения оплаты')


# @router.message(CardPay.successfulphoto)
# async def successfulphoto(message: Message, state: FSMContext, bot: Bot):
#     await state.update_data(payphotocheck=message.photo[-1].file_id)
#     await bot.send_message(message.from_user.id, 'Ожидайте подтверждение вашей оплаты админом')
#     data = await state.get_data()
#     payphotocheck = data.get('payphotocheck')
#     await bot.send_photo(chat_id=intadmin_id, caption='Проверьте оплату на корректность:', photo=payphotocheck, reply_markup=kb.checkpaymentscorrectkeyboard)


# @router.callback_query(F.data.startswith('True'))
# async def Trueanswer(callback: CallbackQuery):
#     await callback.answer()
#     await callback.message.answer('Отправляю гайд счастливчику🥳')
#     gaidsell = await rq.get_gaid(getgaid)
#     for gaid in gaidsell:
#         await callback.answer_document(chat_id=clientid, document=gaid.fail)






