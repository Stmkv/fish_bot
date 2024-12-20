from functools import partial

import redis
from email_validator import EmailNotValidError, validate_email
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
    connect_client_to_cart,
    create_client,
    delete_product_items,
    get_cart_id,
    get_image,
    get_picture_url,
    get_products,
    get_products_cart,
)


def start(update, context, strapi_api_token):
    products = get_products(strapi_api_token, url_starpi)
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


def handle_menu(update: Update, context: CallbackContext, strapi_api_token) -> None:
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

    products = get_products(strapi_api_token, url_starpi)
    picture_url = get_picture_url(strapi_api_token, str(query.data), url_starpi)
    image_bytes = get_image(strapi_api_token, picture_url, url_starpi)
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


def handle_description(update: Update, context: CallbackContext, strapi_api_token):
    query = update.callback_query
    query.answer()
    if query.data == "back":
        start(update, context, strapi_api_token)
        return "HANDLE_MENU"
    if query.data == "in_cart":
        product_id = context.user_data["product_id"]

        cart_item_id = add_to_cart_item(
            strapi_api_token, str(query.message.chat_id), product_id, url_starpi
        )
        cart_id = get_cart_id(strapi_api_token, str(query.message.chat_id), url_starpi)

        connect_cart_to_cart_item(strapi_api_token, cart_id, cart_item_id, url_starpi)
        context.user_data[product_id] = ""
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Товар добавлен в корзину",
        )
        start(update, context, strapi_api_token)
        return "HANDLE_MENU"

    if query.data == "chek_cart":
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        check_cart(update, context, strapi_api_token)
        return "GET_CART_MENU"


def get_cart_menu(update: Update, context: CallbackContext, strapi_api_token):
    query = update.callback_query
    query.answer()
    tg_id = query.message.chat_id
    user_cart = get_products_cart(
        strapi_api_token, str(query.message.chat_id), url_starpi
    )
    if query.data == "clear_cart":
        delete_product_items(strapi_api_token, tg_id, user_cart, url_starpi)
        start(update, context, strapi_api_token)
        return "HANDLE_MENU"
    if query.data == "in_menu":
        start(update, context, strapi_api_token)
        return "HANDLE_MENU"
    if query.data == "pay":
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Пожалуйства введите ваш email для связи",
        )
        return "WAIT_EMAIL"


def wait_email(update: Update, context: CallbackContext, strapi_api_token):
    chat_id = update.effective_user.id
    email = update.message.text
    try:
        validate_email(email)
    except EmailNotValidError:
        context.bot.send_message(
            chat_id=chat_id,
            text="Некорректный email, попробуйте еще раз",
        )
        return "WAIT_EMAIL"
    tg_id = str(update.effective_user.id)
    client_id = create_client(strapi_api_token, tg_id, email, url_starpi)
    cart_id = get_cart_id(strapi_api_token, chat_id, url_starpi)
    connect_client_to_cart(strapi_api_token, client_id, cart_id, url_starpi)
    context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Спасибо, менеджер скоро с вами свяжется ",
    )
    start(update, context, strapi_api_token)
    return "HANDLE_MENU"


def check_cart(update: Update, context: CallbackContext, strapi_api_token):
    keyboard = [
        [
            InlineKeyboardButton("Отказаться от товара", callback_data="clear_cart"),
            InlineKeyboardButton("В главное меню", callback_data="in_menu"),
        ],
        [InlineKeyboardButton("Оплатить", callback_data="pay")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_cart = get_products_cart(
        strapi_api_token, str(update.effective_user.id), url_starpi
    )
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


def handle_users_reply(update, context, strapi_api_token, db, url_starpi):
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
        "START": partial(start, strapi_api_token=strapi_api_token),
        "HANDLE_MENU": partial(handle_menu, strapi_api_token=strapi_api_token),
        "HANDLE_DESCRIPTION": partial(
            handle_description, strapi_api_token=strapi_api_token
        ),
        "GET_CART_MENU": partial(get_cart_menu, strapi_api_token=strapi_api_token),
        "WAIT_EMAIL": partial(wait_email, strapi_api_token=strapi_api_token),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)

        user_state = db.get(chat_id).decode("utf-8")
    except Exception as err:
        print(err)


if __name__ == "__main__":
    env = Env()
    env.read_env()
    tg_bot_token = env.str("TG_BOT_TOKEN")
    strapi_api_token = env.str("STRAPI_API_TOKEN")

    url_starpi = env.str("URL_STARPI")
    database_password = env.str("REDIS_PASSWORD")
    database_host = env.str("REDIS_ADDRESS")
    database_port = env.str("REDIS_PORT")
    database = redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password,
    )

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CommandHandler(
            "start",
            partial(
                handle_users_reply,
                strapi_api_token=strapi_api_token,
                db=database,
                url_starpi=url_starpi,
            ),
        )
    )
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(
                handle_users_reply,
                strapi_api_token=strapi_api_token,
                db=database,
                url_starpi=url_starpi,
            ),
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(
                handle_users_reply,
                strapi_api_token=strapi_api_token,
                db=database,
                url_starpi=url_starpi,
            ),
        )
    )
    updater.start_polling()
    updater.idle()
