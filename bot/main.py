import asyncio
import logging
import os

from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Update
from handlers.starthandler import router
from database.models import async_main
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from utils.commands import set_commands
from admin.handlerauthadmin import authorization_start
from admin.handleradddatagaid import adddescriptiongaid, addpole, addphoto, addnamefail, addfail, addpricecardgaid, addpricestargaid
from admin.handleradddatakurs import addpoleurl, addnameurl, addurl, addpricecardkurs, addpricestarkurs, adddescriptionkurs
from admin.handlerdelitdatagaid import deletegaid, gaiddelit
from admin.handlerdelitdatakurs import deletekurs, kursdelit
from handlers.outputhandlergaid import gaid_start, gaidselect,buygaid, successful_paymentgaid, pre_checkout_querygaid, payphotocheckget, Trueanswer, Falseanswer, Confirmanswer, UnConfirmanswer, UnConfirmanswerno, ConfirmanswerYes, successfulphoto
from handlers.outputhandlerkurs import kurs_start, kursselect, buykurs, successful_paymentkurs, pre_checkout_querykurs, payphotocheckgetkurs, successfulphotokurs, Trueanswerkurs, Falseanswerkurs, Confirmanswerkurs, UnConfirmanswerkurs, ConfirmanswerYeskurs, UnConfirmanswernokurs
from admin.sendall import rassilka, kurs, kurssendall, gaids, gaidsendall
from admin.custom_sendall import function_custom_message, get_custom_message
from admin.statistic import statistica

from aiogram.filters import Command
from admin.handleradddatagaid import AddGaid
from admin.handleradddatakurs import AddKurs
from admin.custom_sendall import Custom_message
from handlers.outputhandlergaid import Card_Pay_gaid
from handlers.outputhandlerkurs import Card_Pay_kurs


load_dotenv('./.env')


IS_WEBHOOK = 1

token = os.getenv('TOKEN')
NGINX_HOST = os.getenv('NGINX_HOST') 

# webhook settings
WEBHOOK_HOST = f'https://{NGINX_HOST}'
WEBHOOK_PATH = '/webhook'

# webserver settings
WEBAPP_HOST = '0.0.0.0' 
WEBAPP_PORT = 7111 #3001


bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()


async def send_error_notification(bot: Bot, error: Exception):
    """
    Отправляет уведомление администратору об ошибке.
    """
    admin_id = os.getenv('ADMIN_ID')
    if not admin_id:
        logging.error("ADMIN_ID не установлен в .env файле!")
        return
        
    try:
        error_message = (
            "⚠️ <b>Произошла ошибка в боте!</b>\n\n"
            f"<b>Тип ошибки:</b> <code>{type(error).__name__}</code>\n"
            f"<b>Описание:</b> <code>{str(error)}</code>\n\n"
            "Проверьте логи для деталей."
        )
        await bot.send_message(admin_id, error_message)
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление об ошибке: {e}")


async def errors_handler(update: Update, exception: Exception) -> bool:
    """
    Обработчик необработанных исключений.
    Логирует ошибку и отправляет уведомление администратору.
    """
    logging.exception(f"Необработанное исключение в обработчике: {exception}")
    
    try:
        await send_error_notification(bot, exception)
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление об ошибке: {e}")
    
    return True


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(url=f"{WEBHOOK_HOST}{WEBHOOK_PATH}",
        drop_pending_updates=True
        )
    print(f'Telegram servers now send updates to {WEBHOOK_HOST}{WEBHOOK_PATH}. Bot is online')


# async def on_shutdown(bot: Bot) -> None:
#     await bot.delete_webhook()  

async def delete_webhook():
    bot = Bot(token=token) 
    await bot.delete_webhook()
    await bot.session.close()



dp.message.register(authorization_start, Command(commands='adminsettings'))

dp.callback_query.register(addpole, F.data.startswith('keyboardaddgaid'))
dp.message.register(addnamefail, AddGaid.namefail)
dp.message.register(addphoto, AddGaid.photo)
dp.message.register(addfail, AddGaid.fail)
dp.message.register(adddescriptiongaid, AddGaid.descriptiongaid)
dp.message.register(addpricecardgaid, AddGaid.pricecardgaid)
dp.message.register(addpricestargaid, AddGaid.pricestargaid)

dp.message.register(gaid_start, Command(commands='gaid'))
dp.callback_query.register(gaidselect, F.data.startswith('selectgaid_'))
dp.callback_query.register(buygaid, F.data.startswith('stars_gaid'))
dp.pre_checkout_query.register(pre_checkout_querygaid)
dp.message.register(successful_paymentgaid, F.successful_payment.invoice_payload == 'gaids')

dp.callback_query.register(deletegaid, F.data.startswith('keyboarddeletegaid'))
dp.callback_query.register(gaiddelit, F.data.startswith('delitgaid_'))


dp.callback_query.register(addpoleurl, F.data.startswith('keyboardaddkurs'))
dp.message.register(addnameurl, AddKurs.nameurl)
dp.message.register(addurl, AddKurs.url)
dp.message.register(adddescriptionkurs, AddKurs.descriptionkurs)
dp.message.register(addpricecardkurs, AddKurs.pricecardkurs)
dp.message.register(addpricestarkurs, AddKurs.pricestarkurs)


dp.message.register(kurs_start, Command(commands='kurs'))
dp.callback_query.register(kursselect, F.data.startswith('selectkurs_'))
dp.callback_query.register(buykurs, F.data.startswith('stars_kurs'))
dp.pre_checkout_query.register(pre_checkout_querykurs)
dp.message.register(successful_paymentkurs, F.successful_payment.invoice_payload == 'kurs')

dp.callback_query.register(deletekurs, F.data.startswith('keyboarddeletekurs'))
dp.callback_query.register(kursdelit, F.data.startswith('delitkurs_'))


dp.callback_query.register(rassilka, F.data.startswith('keyboardrassilka'))
dp.callback_query.register(kurs, F.data == 'sendkurs')
dp.callback_query.register(kurssendall, F.data.startswith('sendkurs_'))
dp.callback_query.register(gaids, F.data == 'sendgaids')
dp.callback_query.register(gaidsendall, F.data.startswith('sendgaid_'))
dp.callback_query.register(function_custom_message, F.data == 'custom_message')
dp.message.register(get_custom_message, Custom_message.msg_custom)

dp.callback_query.register(statistica, F.data.startswith('keyboardstatistika'))

dp.callback_query.register(payphotocheckget, F.data.startswith('cards_gaid'))
dp.message.register(successfulphoto, Card_Pay_gaid.successful_photo_gaid)
dp.callback_query.register(Trueanswer, F.data.startswith('true_gaid'))
dp.callback_query.register(Falseanswer, F.data.startswith('false_gaid'))
dp.callback_query.register(Confirmanswer, F.data.startswith('yes_false_gaid'))
dp.callback_query.register(UnConfirmanswer, F.data.startswith('no_false_gaid'))
dp.callback_query.register(ConfirmanswerYes, F.data.startswith('ok_gaid'))
dp.callback_query.register(UnConfirmanswerno, F.data.startswith('no_gaid'))

dp.callback_query.register(payphotocheckgetkurs, F.data.startswith('cards_kurs'))
dp.message.register(successfulphotokurs, Card_Pay_kurs.successful_photo_kurs)
dp.callback_query.register(Trueanswerkurs, F.data.startswith('true_kurs'))
dp.callback_query.register(Falseanswerkurs, F.data.startswith('false_kurs'))
dp.callback_query.register(Confirmanswerkurs, F.data.startswith('yes_false_kurs'))
dp.callback_query.register(UnConfirmanswerkurs, F.data.startswith('no_false_kurs'))
dp.callback_query.register(ConfirmanswerYeskurs, F.data.startswith('ok_kurs'))
dp.callback_query.register(UnConfirmanswernokurs, F.data.startswith('no_kurs'))

dp.errors.register(errors_handler)

# dp.startup.register(on_startup)
# dp.shutdown.register(on_shutdown)

dp.include_router(router)

async def healthcheck(request: web.Request) -> web.Response:
    """Endpoint для проверки работоспособности бота"""
    print("Healthcheck endpoint called")  # Добавьте эту строку
    return web.Response(text="OK", status=200)

    
async def main() -> None:
    print("Бот запущен! Проверка вебхука...")
    await bot.set_webhook(url=f"{WEBHOOK_HOST}{WEBHOOK_PATH}")
    print(f"Вебхук установлен на {WEBHOOK_HOST}{WEBHOOK_PATH}")
    await async_main()
    await delete_webhook()
    await set_commands(bot)
    
    if IS_WEBHOOK == 1:
        await asyncio.sleep(5)

        # Создаем один сервер с обоими обработчиками
        app = web.Application()
        
        # Добавляем healthcheck
        app.router.add_get('/health', healthcheck)
        
        # Добавляем webhook
        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT).start()
        
        print(f"Бот запущен на {WEBHOOK_HOST}")
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            print("\nПолучен сигнал остановки...")
        except Exception as e:  # <-- ДОБАВЛЯЕМ ОБРАБОТКУ ДРУГИХ ИСКЛЮЧЕНИЙ
            print(f"\nКритическая ошибка: {e}")
        finally:  # <-- ЭТОТ БЛОК ВЫПОЛНИТСЯ В ЛЮБОМ СЛУЧАЕ
            print("Останавливаем бота...")
            await bot.session.close()
            if IS_WEBHOOK == 1:
                await runner.cleanup()
            print("Бот успешно остановлен")
    else:
        try:
            await dp.start_polling(bot)
        except KeyboardInterrupt:
            print("\nПолучен сигнал остановки...")
        except Exception as e:  # <-- ОБРАБОТКА ДЛЯ POLLING РЕЖИМА
            logging.exception("Критическая ошибка в боте:")
            await send_error_notification(bot, e)
            raise  # Повторно поднимаем исключение для завершения работы
        finally:
            print("Останавливаем бота...")
            await bot.session.close()
            await dp.storage.close()
            print("Бот успешно остановлен")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
    