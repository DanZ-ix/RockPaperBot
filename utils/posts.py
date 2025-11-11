import logging

from aiogram import types

from loader import bot


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
        elif new_message.video:
            await bot.send_video(
                chat_id=user_id,
                video=new_message.video.file_id,
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

    except Exception as e:
        logging.error(f"Ошибка при отправке поста {ad_post.get('_id')} пользователю {user_id}: {e}")
