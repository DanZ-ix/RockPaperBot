
from loader import messages_collection, admin_collection, users_collection, posts_collection, DEFAULT_MESSAGES, bot
from datetime import datetime, timedelta



def get_messages():
    messages = {}
    db_messages = messages_collection.find()
    for msg in db_messages:
        messages[msg['key']] = msg['text']
    return messages


def init_messages():
    for key, text in DEFAULT_MESSAGES.items():
        existing_message = messages_collection.find_one({'key': key})
        if not existing_message:
            messages_collection.insert_one({'key': key, 'text': text})


def get_message(key):
    msg = messages_collection.find_one({'key': key})
    return msg['text'] if msg else DEFAULT_MESSAGES.get(key, '')


def is_admin(user_id):
    admin_user = admin_collection.find_one({'user_id': str(user_id)})
    return admin_user is not None


async def save_user(user, referrer_id=None):
    existing_user = users_collection.find_one({'user_id': str(user.id)})
    if existing_user:
        users_collection.update_one(
            {'user_id': str(user.id)},
            {'$set': {'last_activity': datetime.now()}}
        )
        return existing_user

    bot_info = await bot.get_me()
    bot_username = bot_info.username

    user_data = {
        'user_id': str(user.id),
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'is_ready': False,
        'is_playing': False,
        'referral_link': f"https://t.me/{bot_username}?start={user.id}",
        'referrer_id': referrer_id,
        'referral_count': 0,
        'posts_sent': [],
        'game_wins': 0,
        'game_losses': 0,
        'game_draws': 0
    }

    users_collection.insert_one(user_data)

    if referrer_id:
        users_collection.update_one(
            {'user_id': str(referrer_id)},
            {'$inc': {'referral_count': 1}}
        )

    return user_data


def get_user(user_id):
    return users_collection.find_one({'user_id': str(user_id)})


def update_user_activity(user_id, is_playing=None):
    update_data = {'last_activity': datetime.now()}
    if is_playing is not None:
        update_data['is_playing'] = is_playing
    users_collection.update_one(
        {'user_id': str(user_id)},
        {'$set': update_data}
    )


# ==================== РАБОТА С ПОСТАМИ ====================

def save_ad_post(message_data):
    message_json = message_data.reply_to_message.to_python()
    result = posts_collection.insert_one(message_json)
    return result.inserted_id


def get_all_ad_posts():
    return list(posts_collection.find().sort('created_at', -1))




