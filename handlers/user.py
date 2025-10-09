
import asyncio
import logging
import random
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from loader import dp, bot, UserStates, GAME_CHOICES, rock, scissors, paper, GAME_RULES

from utils.database import save_user, update_user_activity, get_message, users_collection, posts_collection, get_user, \
    get_all_ad_posts
from utils.keyboards import get_main_keyboard, get_ready_keyboard, get_game_keyboard


@dp.message_handler(commands=['start'], state='*')
async def start_command(message: types.Message, state: FSMContext):
    await state.finish()
    user = message.from_user

    referral_id = None
    args = message.text.split()
    if len(args) > 1:
        referral_id = args[1]
        if referral_id == str(user.id):
            referral_id = None  # нельзя быть своим рефералом

    user_data = await save_user(user, referral_id)
    update_user_activity(user.id)

    welcome_text = get_message('welcome')

    await message.answer(welcome_text, reply_markup=get_main_keyboard())
    await message.answer(get_message('ready_question'), reply_markup=get_ready_keyboard())
    await UserStates.AWAITING_READY.set()


@dp.message_handler(lambda message: message.text.lower() == 'да', state=UserStates.AWAITING_READY)
async def ready_yes(message: types.Message, state: FSMContext):
    users_collection.update_one(
        {'user_id': str(message.from_user.id)},
        {'$set': {'is_ready': True, 'is_playing': True}}
    )
    update_user_activity(message.from_user.id, is_playing=True)

    await message.answer("Отлично! Давайте сыграем в камень-ножницы-бумага!\nПобедишь, получишь вакансию", reply_markup=get_game_keyboard())
    await UserStates.PLAYING_GAME.set()


@dp.message_handler(lambda message: message.text.lower() == 'нет', state=UserStates.AWAITING_READY)
async def ready_no(message: types.Message, state: FSMContext):
    users_collection.update_one(
        {'user_id': str(message.from_user.id)},
        {'$set': {'is_ready': False, 'is_playing': False}}
    )
    update_user_activity(message.from_user.id, is_playing=False)

    await message.answer("Хорошо, мы напомним вам позже!", reply_markup=get_main_keyboard())
    await send_all_saved_messages_sequentially(message.from_user.id)
    await state.finish()


async def send_all_saved_messages_sequentially(user_id: str):
    """Отправляет все сообщения из коллекции posts как есть, с паузой 60 секунд."""
    try:
        # Получаем все посты из коллекции `posts` (в вашем коде — это `posts_collection`)
        # Предполагается, что каждый документ — это сохранённый объект Message (в формате to_python())
        posts = list(posts_collection.find().sort('created_at', 1))

        if not posts:
            return

        for _ in posts:
            # Ждём 1 минуту
            await asyncio.sleep(60)
            res = await send_random_ad_post(user_id)
            if res == "STOP":
                break

    except Exception as e:
        logging.error(f"Ошибка в send_all_saved_messages_sequentially для {user_id}: {e}")




async def send_ad_post(ad_post, user_id):
    try:
        new_message = types.Message.to_object(ad_post)
        if new_message.photo:
            # Берём фото с наибольшим размером
            file_json = sorted(new_message.photo, key=lambda d: d.file_size)[-1]
            await bot.send_photo(
                chat_id=user_id,
                photo=file_json.file_id,
                caption=new_message.caption,
                caption_entities=new_message.caption_entities,
                reply_markup=new_message.reply_markup
            )
        else:
            # Отправляем как текстовое сообщение
            await bot.send_message(
                chat_id=user_id,
                text=new_message.text,
                entities=new_message.entities,
                reply_markup=new_message.reply_markup,
                disable_web_page_preview=True
            )
        users_collection.update_one(
            {'user_id': str(user_id)},
            {'$addToSet': {'posts_sent': str(ad_post['_id'])}}
        )

    except Exception as e:
        logging.error(f"Ошибка при отправке поста {ad_post.get('_id')} пользователю {user_id}: {e}")


async def send_random_ad_post(user_id):
    try:
        user_data = get_user(user_id)
        sent_post_ids = set(str(pid) for pid in user_data.get('posts_sent', [])) if user_data else set()

        # Получаем все посты
        all_posts = get_all_ad_posts()
        # Фильтруем: только те, что ещё не отправлялись
        available_posts = [post for post in all_posts if str(post['_id']) not in sent_post_ids]

        if available_posts:
            random_post = random.choice(available_posts)
            await send_ad_post(random_post, user_id)
        else:
            # Опционально: можно ничего не отправлять или отправить заглушку
            return "STOP"
    except Exception as e:
        logging.error(f"Ошибка при отправке поста пользователю {user_id}: {e}")



@dp.message_handler(lambda message: message.text.lower() in [rock, scissors, paper],
                    state=UserStates.PLAYING_GAME)
async def play_game(message: types.Message, state: FSMContext):
    user_choice = message.text.lower()
    bot_choice = random.choice(GAME_CHOICES)

    if user_choice == bot_choice:
        result = 'draw'
        result_text = get_message('game_draw')
        users_collection.update_one({'user_id': str(message.from_user.id)}, {'$inc': {'game_draws': 1}})
    elif GAME_RULES[user_choice] == bot_choice:
        result = 'win'
        result_text = get_message('game_win')
        users_collection.update_one({'user_id': str(message.from_user.id)}, {'$inc': {'game_wins': 1}})
    else:
        result = 'lose'
        result_text = get_message('game_lose')
        users_collection.update_one({'user_id': str(message.from_user.id)}, {'$inc': {'game_losses': 1}})

    update_user_activity(message.from_user.id, is_playing=True)

    await message.answer(f"Вы выбрали: {user_choice}\nБот выбрал: {bot_choice}\n{result_text}")

    ad_posts = get_all_ad_posts()
    if ad_posts:
        await send_random_ad_post(message.from_user.id)

    await message.answer("Хотите сыграть еще раз?", reply_markup=get_ready_keyboard())
    await UserStates.AWAITING_READY.set()


@dp.message_handler(lambda message: message.text == 'Удвой свой заработок')
async def double_earnings(message: types.Message):
    update_user_activity(message.from_user.id)
    await message.answer(
        get_message('double_offer'),
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton('Подписаться', url=get_message('channel_link'))
        )
    )

