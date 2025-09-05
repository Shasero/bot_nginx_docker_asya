import asyncio
import logging
import os
import sys
import io

from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from handlers.starthandler import router
from database.models import async_main
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.memory import MemoryStorage
from utils.commands import set_commands
from admin.handlerauthadmin import authorization_start
from admin.handler_add_data import add_gaid, add_gaid_name, add_gaid_photo, add_gaid_description, add_gaid_file, add_gaid_price_card, add_gaid_price_star, add_kurs
from admin. handler_delit_data import start_on_delit_gaid, drop_gaid, start_on_delit_kurs, drop_kurs
from handlers.handler_output_data import gaid_start, gaid_select, buy_gaid, successful_payment_gaid, pre_checkout_query_gaid, pay_photo_check_get_gaid, Trueanswer, Falseanswer, Confirmanswer, UnConfirmanswer, UnConfirmanswerno, ConfirmanswerYes, successful_photo_gaid, kurs_start, kurs_select, buy_kurs, successful_payment_kurs, pay_photo_check_get_kurs, successful_photo_kurs, Trueanswerkurs, Falseanswerkurs, Confirmanswerkurs, UnConfirmanswerkurs, ConfirmanswerYeskurs, UnConfirmanswernokurs
from admin.sendall import rassilka, kurs, kurssendall, gaids, gaidsendall
from admin.custom_sendall import function_custom_message, get_custom_message
from admin.statistic import statistica

from aiogram.filters import Command
from admin.handler_add_data import AddDataStates
from admin.custom_sendall import Custom_message
from handlers.handler_output_data import CardPayStates


load_dotenv('./.env')


IS_WEBHOOK = 1

token = os.getenv('TOKEN')
NGINX_HOST = os.getenv('NGINX_HOST') 

# webhook settings
WEBHOOK_HOST = f'https://{NGINX_HOST}'
WEBHOOK_PATH = '/webhook'

# webserver settings
WEBAPP_HOST = '0.0.0.0' 
WEBAPP_PORT = 7111

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

storage = MemoryStorage()

dp = Dispatcher(storage=storage)


async def cleanup_old_states():
    while True:
        await asyncio.sleep(3600)


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
            f"<b>Описание:</b> <code>{str(error)[:100]}...</code>\n\n"
            "Проверьте логи для деталей."
        )
        await bot.send_message(admin_id, error_message)
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление об ошибке: {e}")


async def errors_handler(exception: Exception) -> bool:
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

dp.callback_query.register(add_gaid, F.data.startswith('keyboardaddgaid'))
dp.message.register(add_gaid_name, AddDataStates.name)
dp.message.register(add_gaid_photo, AddDataStates.photo)
dp.message.register(add_gaid_description, AddDataStates.description)
dp.message.register(add_gaid_file, AddDataStates.file)
dp.message.register(add_gaid_price_card, AddDataStates.price_card)
dp.message.register(add_gaid_price_star, AddDataStates.price_star)

dp.message.register(gaid_start, Command(commands='gaid'))
dp.callback_query.register(gaid_select, F.data.startswith('selectgaid_'))
dp.callback_query.register(buy_gaid, F.data.startswith('stars_gaid'))
dp.pre_checkout_query.register(pre_checkout_query_gaid)
dp.message.register(successful_payment_gaid, F.successful_payment.invoice_payload == 'gaid')
dp.callback_query.register(pay_photo_check_get_gaid, F.data.startswith('cards_gaid'))
dp.message.register(successful_photo_gaid, CardPayStates.successful_photo_gaid)

dp.callback_query.register(start_on_delit_gaid, F.data.startswith('keyboard_delete_gaid'))
dp.callback_query.register(drop_gaid, F.data.startswith('delitg_'))


dp.callback_query.register(add_kurs, F.data.startswith('keyboardaddkurs'))


dp.message.register(kurs_start, Command(commands='kurs'))
dp.callback_query.register(kurs_select, F.data.startswith('selectkurs_'))
dp.callback_query.register(buy_kurs, F.data.startswith('stars_kurs'))
dp.message.register(successful_payment_kurs, F.successful_payment.invoice_payload == 'kurs')

# dp.message.register(cancel_any_state, Command(commands=['gaid', 'kurs']))

dp.callback_query.register(start_on_delit_kurs, F.data.startswith('keyboard_delete_kurs'))
dp.callback_query.register(drop_kurs, F.data.startswith('delitk_'))


dp.callback_query.register(rassilka, F.data.startswith('keyboardrassilka'))
dp.callback_query.register(kurs, F.data == 'sendkurs')
dp.callback_query.register(kurssendall, F.data.startswith('sendkurs_'))
dp.callback_query.register(gaids, F.data == 'sendgaids')
dp.callback_query.register(gaidsendall, F.data.startswith('sendgaid_'))
dp.callback_query.register(function_custom_message, F.data == 'custom_message')
dp.message.register(get_custom_message, Custom_message.msg_custom)

dp.callback_query.register(statistica, F.data.startswith('keyboardstatistika'))

dp.callback_query.register(pay_photo_check_get_gaid, F.data.startswith('cards_gaid'))
dp.message.register(successful_photo_gaid, CardPayStates.successful_photo_gaid)
dp.callback_query.register(Trueanswer, F.data.startswith('true_gaid'))
dp.callback_query.register(Falseanswer, F.data.startswith('false_gaid'))
dp.callback_query.register(Confirmanswer, F.data.startswith('yes_false_gaid'))
dp.callback_query.register(UnConfirmanswer, F.data.startswith('no_false_gaid'))
dp.callback_query.register(ConfirmanswerYes, F.data.startswith('ok_gaid'))
dp.callback_query.register(UnConfirmanswerno, F.data.startswith('no_gaid'))

dp.callback_query.register(pay_photo_check_get_kurs, F.data.startswith('cards_kurs'))
dp.message.register(successful_photo_kurs, CardPayStates.successful_photo_kurs)
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
    return web.Response(text="OK", status=200)

    
async def main() -> None:
    print("Бот запущен! Проверка вебхука...")
    await async_main()
    await set_commands(bot)
    
    if IS_WEBHOOK == 1:
        print("Запуск в режиме WEBHOOK...")

        await bot.delete_webhook()
        
        
        try:
            await bot.set_webhook(
                url=f"{WEBHOOK_HOST}{WEBHOOK_PATH}",
                drop_pending_updates=True
            )
            print(f"Вебхук установлен на {WEBHOOK_HOST}{WEBHOOK_PATH}")
        except Exception as e:
            print(f"Ошибка при установке вебхука: {e}")
            return

        app = web.Application()
        app.router.add_get('/health', healthcheck)
        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
        await site.start()
        
        print(f"Бот запущен на {WEBHOOK_HOST}")
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            print("\nПолучен сигнал остановки...")
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
        finally:
            print("Останавливаем бота...")
            await bot.session.close()
            await runner.cleanup()
            print("Бот успешно остановлен")
    else:
        print("Запуск в режиме POLLING...")

        try:
            await bot.delete_webhook(drop_pending_updates=True)
            print("Вебхук удален (если был установлен)")
        except Exception as e:
            print(f"Ошибка при удалении вебхука: {e}")

        try:
            await dp.start_polling(bot)
        except KeyboardInterrupt:
            print("\nПолучен сигнал остановки...")
        except Exception as e:
            logging.exception("Критическая ошибка в боте:")
            await send_error_notification(bot, e)
            raise
        finally:
            print("Останавливаем бота...")
            await bot.session.close()
            await dp.storage.close()
            print("Бот успешно остановлен")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(main())
        asyncio.create_task(cleanup_old_states())
    except KeyboardInterrupt:
        print("\nБот был остановлен пользователем")
    