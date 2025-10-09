
import asyncio
import os
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from bson import ObjectId

from loader import dp, UserStates, AdminStates, messages_collection

from utils.database import users_collection, is_admin, posts_collection, get_user, \
    get_all_ad_posts, get_messages, save_ad_post
from utils.keyboards import get_main_keyboard, get_admin_keyboard



@dp.message_handler(commands=['admin'], state='*')
async def admin_command(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Админ-панель", reply_markup=get_admin_keyboard())
    else:
        await message.answer("У вас нет доступа к админ-панели")


@dp.message_handler(lambda message: message.text == '📊 Выгрузить базу', state='*')
async def export_database(message: types.Message):
    if not is_admin(message.from_user.id): return

    try:
        users = list(users_collection.find())
        users_text = "Список пользователей:\n\n"
        for user in users:
            users_text += f"{user['user_id']}\n"
        filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(users_text)

        await message.answer_document(open(filename, 'rb'))
        os.remove(filename)
    except Exception as e:
        await message.answer(f"Ошибка при выгрузке: {e}")


@dp.message_handler(lambda message: message.text == '📈 Реферальная статистика', state='*')
async def referral_stats(message: types.Message):
    if not is_admin(message.from_user.id): return

    top_referrers = list(users_collection.find({'referral_count': {'$gt': 0}}).sort('referral_count', -1).limit(10))
    if not top_referrers:
        await message.answer("Пока нет пользователей с рефералами")
        return

    stats_text = "🏆 Топ рефералов:\n\n"
    for i, user in enumerate(top_referrers, 1):
        stats_text += f"{i}. {user.get('first_name', 'Пользователь')} (@{user.get('username', 'нет')})\n"
        stats_text += f"   Приглашено: {user.get('referral_count', 0)}\n"
        stats_text += f"   Ссылка: {user.get('referral_link', '')}\n\n"

    await message.answer(stats_text)


@dp.message_handler(lambda message: message.text == '📝 Изменить сообщения', state='*')
async def change_messages(message: types.Message):
    if not is_admin(message.from_user.id): return

    messages = get_messages()
    messages_text = "Текущие сообщения (введите ключ для изменения):\n\n"
    for key, value in messages.items():
        messages_text += f"🔑 {key}\n📝 {value[:100]}{'...' if len(value) > 100 else ''}\n\n"

    await message.answer(messages_text)
    await AdminStates.AWAITING_MESSAGE_KEY.set()


@dp.message_handler(state=AdminStates.AWAITING_MESSAGE_KEY)
async def process_message_key(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await UserStates.AWAITING_READY.set()
        return

    key = message.text.strip()
    existing = messages_collection.find_one({'key': key})
    if not existing:
        await UserStates.AWAITING_READY.set()
        await message.answer("Такого ключа нет")
        return

    await state.update_data(editing_key=key)
    await message.answer(f"Введите новый текст для сообщения '{key}':")
    await AdminStates.AWAITING_NEW_MESSAGE_TEXT.set()


@dp.message_handler(state=AdminStates.AWAITING_NEW_MESSAGE_TEXT)
async def process_new_message_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return

    user_data = await state.get_data()
    key = user_data['editing_key']
    new_text = message.text

    messages_collection.update_one({'key': key}, {'$set': {'text': new_text}})
    await message.answer(f"✅ Сообщение '{key}' успешно обновлено!")
    await state.finish()
    await message.answer("Админ-панель", reply_markup=get_admin_keyboard())


@dp.message_handler(lambda message: message.text == '➕ Добавить рекламный пост', state='*')
async def add_ad_post(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Перешлите рекламный пост (с кнопками, картинками и т.д.):")
    await AdminStates.AWAITING_POST_FORWARD.set()



@dp.message_handler(state=AdminStates.AWAITING_POST_FORWARD, content_types=types.ContentTypes.ANY)
async def receive_forwarded_post(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return

    try:
        post_id = save_ad_post(message)
        await message.answer(f"✅ Рекламный пост успешно сохранен! ID: {post_id}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.finish()
        await message.answer("Админ-панель", reply_markup=get_admin_keyboard())


@dp.message_handler(lambda message: message.text == '📋 Список рекламных постов', state='*')
async def list_ad_posts(message: types.Message):
    if not is_admin(message.from_user.id): return

    posts = get_all_ad_posts()
    if not posts:
        await message.answer("Нет сохраненных рекламных постов")
        return

    for i, post in enumerate(posts, 1):
        preview = (post.get('caption') or post.get('text') or 'Без текста')[:100]
        info = f"📌 Пост #{i}\nID: {post['_id']}\n{preview}..."
        await message.answer(info)
        await asyncio.sleep(0.1)  # чтобы не спамить


@dp.message_handler(lambda message: message.text == '🗑️ Удалить рекламный пост', state='*')
async def delete_ad_post(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return

    posts = get_all_ad_posts()
    if not posts:
        await message.answer("Нет постов для удаления")
        return

    posts_text = "Введите ID поста для удаления:\n\n"
    for post in posts:
        preview = (post.get('caption') or post.get('text') or 'Без текста')[:50]
        posts_text += f"ID: {post['_id']} — {preview}...\n"

    await message.answer(posts_text)
    await AdminStates.AWAITING_POST_SELECTION.set()
    await state.update_data(deleting_post=True)


@dp.message_handler(state=AdminStates.AWAITING_POST_SELECTION)
async def delete_post(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return

    post_id_str = message.text.strip()

    try:
        post_id = ObjectId(post_id_str)
    except Exception:
        await message.answer("❌ Неверный формат ID. Ожидается валидный ObjectId.")
        return

    post = posts_collection.find_one({'_id': post_id})
    if not post:
        await message.answer("❌ Пост с таким ID не найден.")
        return

    posts_collection.delete_one({'_id': post_id})

    await message.answer(f"✅ Пост {post_id_str} успешно удалён!")
    await state.finish()
    await message.answer("Админ-панель", reply_markup=get_admin_keyboard())



@dp.message_handler(lambda message: message.text == '🔗 Отслеживать ссылки', state='*')
async def track_links(message: types.Message):
    if not is_admin(message.from_user.id): return

    pipeline = [
        {"$match": {"referrer_id": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": "$referrer_id",
            "count": {"$sum": 1},
            "users": {"$push": "$user_id"}
        }}
    ]

    ref_stats = list(users_collection.aggregate(pipeline))
    if not ref_stats:
        await message.answer("Нет данных по реферальным ссылкам")
        return

    text = "🔗 Статистика по реферальным ссылкам:\n\n"
    for stat in ref_stats:
        referrer = get_user(stat['_id'])
        name = f"@{referrer.get('username', 'id' + str(stat['_id']))}" if referrer else f"id{stat['_id']}"
        text += f"👤 {name}: привлек {stat['count']} пользователей\n"
        text += f"Ссылка: {referrer.get('referral_link', 'N/A') if referrer else 'N/A'}\n\n"

    await message.answer(text)


@dp.message_handler(lambda message: message.text == '⬅️ Назад', state='*')
async def back_to_main(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Главное меню", reply_markup=get_main_keyboard())
