from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    commands = [
        # BotCommand(
        #     command='start',
        #     description='🚀Запуск бота🤖'
        # ),
        BotCommand(
            command='gaid',
            description='Гайды📖'
        ),
        BotCommand(
            command='kurs',
            description='Курсы🤓'
        )
    ]


    await bot.set_my_commands(commands, BotCommandScopeDefault())