# -*- coding: utf-8 -*-


from aiogram.utils import executor
from handlers import dp
from utils.database import init_messages


async def on_startup(dp):
    init_messages()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
