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

from strapi import (
    add_to_cart_item,
    connect_cart_to_cart_item,
    delete_product_items,
    get_cart_id,
    get_image,
    get_picture_url,
    get_products,
    get_products_cart,
)

_database = None


def start(update, context, api_token_salt):
    products = get_products(api_token_salt)
    keyboard = [
        [InlineKeyboardButton(product["title"], callback_data=product["documentId"])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text(text="Выберете товар 👋", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        query = update.callback_query
        query.message.reply_text(text="Список товаров", reply_markup=reply_markup)

    return "HANDLE_MENU"


def handle_menu(update: Update, context: CallbackContext, api_token_salt) -> None:
    query = update.callback_query
    context.user_data["product_id"] = str(query.data)

    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )

    keyboard = [
        [
            InlineKeyboardButton("Назад", callback_data="back"),
            InlineKeyboardButton("Моя корзина", callback_data="chek_cart"),
        ],
        [InlineKeyboardButton("Добавить в корзину", callback_data="in_cart")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    products = get_products(api_token_salt)
    picture_url = get_picture_url(api_token_salt, str(query.data))
    image_bytes = get_image(api_token_salt, picture_url)
    for product in products:
        if str(product["documentId"]) == str(query.data):
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
    query.answer()
    if query.data == "back":
        start(update, context, api_token_salt)
        return "HANDLE_MENU"
    if query.data == "in_cart":
        product_id = context.user_data["product_id"]

        cart_item_id = add_to_cart_item(
            api_token_salt, str(query.message.chat_id), product_id
        )
        cart_id = get_cart_id(api_token_salt, str(query.message.chat_id))

        connect_cart_to_cart_item(api_token_salt, cart_id, cart_item_id)
        context.user_data[product_id] = ""
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Товар добавлен в корзину",
        )
        start(update, context, api_token_salt)
        return "HANDLE_MENU"

    if query.data == "chek_cart":
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        check_cart(update, context, api_token_salt)
        return "CART_MENU"


def cart_menu(update: Update, context: CallbackContext, api_token_salt):
    query = update.callback_query
    query.answer()
    tg_id = query.message.chat_id
    user_cart = get_products_cart(api_token_salt, str(query.message.chat_id))
    if query.data == "clear_cart":
        delete_product_items(api_token_salt, tg_id, user_cart)
        start(update, context, api_token_salt)
        return "HANDLE_MENU"
    if query.data == "in_menu":
        start(update, context, api_token_salt)
        return "HANDLE_MENU"
    if query.data == "pay":
        ...


def check_cart(update: Update, context: CallbackContext, api_token_salt):
    keyboard = [
        [
            InlineKeyboardButton("Отказаться от товара", callback_data="clear_cart"),
            InlineKeyboardButton("В главное меню", callback_data="in_menu"),
        ],
        [InlineKeyboardButton("Оплатить", callback_data="pay")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_cart = get_products_cart(api_token_salt, str(update.effective_user.id))
    text = ""
    total_sum = 0
    for product in user_cart:
        if product["Product"]:
            text += f"""{product["Product"][0]["title"]} - {product["quantity"]} кг
            {product["Product"][0]["price"]} за кг\n\n"""
            total_sum += product["Product"][0]["price"] * product["quantity"]
    text += f"\n\nОбщая сумма: {total_sum} руб"

    context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=reply_markup,
    )


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
        "CART_MENU": partial(cart_menu, api_token_salt=api_token_salt),
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
