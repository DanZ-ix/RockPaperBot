
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from loader import rock, paper, scissors
from datetime import datetime, timedelta


def get_ready_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    return keyboard

def get_game_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(rock), KeyboardButton(scissors), KeyboardButton(paper))
    keyboard.add(KeyboardButton('Удвой свой заработок'))
    return keyboard


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Удвой свой заработок'))
    return keyboard


def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('📊 Выгрузить базу'))
    keyboard.add(KeyboardButton('📝 Изменить сообщения'))
    keyboard.add(KeyboardButton('➕ Добавить рекламный пост'))
    keyboard.add(KeyboardButton('📋 Список рекламных постов'))
    keyboard.add(KeyboardButton('🗑️ Удалить рекламный пост'))
    keyboard.add(KeyboardButton('📈 Реферальная статистика'))
    keyboard.add(KeyboardButton('🔗 Отслеживать ссылки'))
    keyboard.add(KeyboardButton('⬅️ Назад'))
    return keyboard


