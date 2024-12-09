from ast import keyword
from functools import partial

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from strapi import get_image, get_picture_url, get_products

_database = None


def start(update, context, api_token_salt):
    products = get_products(api_token_salt)
    keyboard = [
        [InlineKeyboardButton(product["title"], callback_data=product["id"])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text(text="Выберете товар 👋", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        query.message.reply_text(text="Список товаров", reply_markup=reply_markup)

    return "HANDLE_MENU"


def handle_menu(update: Update, context: CallbackContext, api_token_salt) -> None:
    query = update.callback_query
    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )

    keyboard = [[InlineKeyboardButton("Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    products = get_products(api_token_salt)
    picture_url = get_picture_url(api_token_salt, str(query.data))
    image_bytes = get_image(api_token_salt, picture_url)
    for product in products:
        if str(product["id"]) == str(query.data):
            text = f"{product["title"]} - {product["price"]} руб/кг\n\n{product["description"]}"
            query.answer()
            context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=image_bytes,
                caption=text,
                reply_markup=reply_markup,
            )
            break
    return "HANDLE_DESCRIPTION"


def handle_description(update: Update, context: CallbackContext, api_token_salt):
    query = update.callback_query
    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )
    query = update.callback_query
    query.answer()
    if query.data == "back":
        start(update, context, api_token_salt)
        return "HANDLE_MENU"


def handle_users_reply(update, context, api_token_salt):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = db.get(chat_id).decode("utf-8")
    states_functions = {
        "START": partial(start, api_token_salt=api_token_salt),
        "HANDLE_MENU": partial(handle_menu, api_token_salt=api_token_salt),
        "HANDLE_DESCRIPTION": partial(
            handle_description, api_token_salt=api_token_salt
        ),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)

        user_state = db.get(chat_id).decode("utf-8")
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = env.str("REDIS_PASSWORD")
        database_host = env.str("REDIS_ADDRESS")
        database_port = env.str("REDIS_PORT")
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password,
        )
    return _database


if __name__ == "__main__":
    env = Env()
    env.read_env()
    tg_bot_token = env.str("TG_BOT_TOKEN")
    api_token_salt = env.str("API_TOKEN_SALT")

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CommandHandler(
            "start", partial(handle_users_reply, api_token_salt=api_token_salt)
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(handle_users_reply, api_token_salt=api_token_salt),
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text, partial(handle_users_reply, api_token_salt=api_token_salt)
        )
    )
    updater.start_polling()
    updater.idle()
