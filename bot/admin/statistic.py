from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, FSInputFile
import os
import json

router = Router()

GAID_DATA_JSON = "gaid_data.json"
KURS_DATA_JSON = "kurs_data.json"
GAID_DATA_TXT = "gaid_data.txt"
KURS_DATA_TXT = "kurs_data.txt"


async def convert_json_to_txt(json_file, txt_file):
    """Converts a JSON file to a TXT file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f_json:
            data = json.load(f_json)

        with open(txt_file, 'w', encoding='utf-8') as f_txt:
            json.dump(data, f_txt, ensure_ascii=False, indent=4)
        return True
    except FileNotFoundError:
        print(f"Error: JSON file {json_file} not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}.")
        return False
    except Exception as e:
        print(f"An error occurred during conversion: {e}")
        return False


@router.callback_query(F.data.startswith('keyboardstatistika'))
async def statistica(callback: CallbackQuery, bot: Bot):
    chat_id = callback.from_user.id
    last_message_id = callback.message.message_id
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.delete_message(chat_id=chat_id, message_id=last_message_id)
    try:
        await callback.message.answer("Отправляю файлы статистики...")

        # Convert JSON to TXT
        gaid_converted = await convert_json_to_txt(GAID_DATA_JSON, GAID_DATA_TXT)
        kurs_converted = await convert_json_to_txt(KURS_DATA_JSON, KURS_DATA_TXT)

        try:
            if gaid_converted and os.path.exists(GAID_DATA_TXT):
                gaid_data_file = FSInputFile(GAID_DATA_TXT)
                await bot.send_document(chat_id=chat_id, document=gaid_data_file)
            else:
                await callback.message.answer( f"Файл {GAID_DATA_JSON} не найден или не удалось его преобразовать.")

            if kurs_converted and os.path.exists(KURS_DATA_TXT):
                kurs_date_file = FSInputFile(KURS_DATA_TXT)
                await bot.send_document(chat_id=chat_id, document=kurs_date_file)
            else:
                await callback.message.answer(f"Файл {KURS_DATA_JSON} не найден или не удалось его преобразовать.")
        except Exception as e:
            await callback.message.answer(f"Произошла ошибка при отправке файлов: {e}")
    except Exception as e:
        print(f"Ошибка в статистике: {e}")

