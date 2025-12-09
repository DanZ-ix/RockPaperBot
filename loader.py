from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

import logging
from pymongo import MongoClient

from utils.configs import bot_token, db_name


MONGO_URI = 'mongodb://localhost:27017/'
DATABASE_NAME = db_name




logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logging.getLogger('aiohttp').setLevel(logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())


# Подключение к MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db.users
posts_collection = db.posts
saved_messages_collection = db.saved_messages
admin_collection = db.admin
messages_collection = db.messages
game_choices_collection = db.choices

# Состояния FSM
class UserStates(StatesGroup):
    AWAITING_READY = State()
    PLAYING_GAME = State()


class AdminStates(StatesGroup):
    AWAITING_POST_FORWARD = State()
    AWAITING_POST_SELECTION = State()
    AWAITING_MESSAGE_KEY = State()
    AWAITING_NEW_MESSAGE_TEXT = State()
    AWAITING_EDIT_POST_ID = State()


# Глобальные переменные для сообщений (только для инициализации)
DEFAULT_MESSAGES = {
    'welcome': 'Привет, спасибо за подписку на бота, давай начнем зарабатывать!',
    'welcome_referral': 'Привет! Вы перешли по реферальной ссылке пользователя {referrer_name}. Добро пожаловать!',
    'ready_question': 'Готов зарабатывать?',
    'game_win': 'Поздравляем! Вы выиграли! Вот ваш приз:',
    'game_lose': 'К сожалению, вы проиграли. Но не расстраивайтесь, вот утешительный приз:',
    'game_draw': 'Ничья! Но мы считаем это победой!',
    'reminder': 'Не забывайте про заработок!',
    'double_offer': 'Подпишитесь на наш канал и удвойте свой заработок!',
    'channel_link': 'https://t.me/your_channel',
    'no_games_left': 'Больше нельзя играть сегодня, приходи завтра',
    'lets_play': 'Отлично! Давайте сыграем в камень-ножницы-бумага!\nПобедишь, получишь вакансию',
    'first_const_button': 'Удвой свой заработок',
    'second_const_button': 'Доступ к быстрому VPN'
}

rock = game_choices_collection.find_one({"name": "rock"}).get("value")
paper = game_choices_collection.find_one({"name": "paper"}).get("value")
scissors = game_choices_collection.find_one({"name": "scissors"}).get("value")

# Игровые элементы
GAME_CHOICES = [rock, scissors, paper]
GAME_RULES = {
    rock: scissors,
    scissors: paper,
    paper: rock
}
