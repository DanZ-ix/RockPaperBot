# -*- coding: utf-8 -*-
import asyncio

from aiogram.utils import executor
from handlers import dp
from utils.database import init_messages, daily_scheduler


async def on_startup(dp):
    init_messages()
    asyncio.create_task(daily_scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
