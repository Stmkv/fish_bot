import logging


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def start_logger(bot, tg_chat_id):
    logger = logging.getLogger("Bot")
    FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        handlers=[TelegramLogsHandler(bot, tg_chat_id)],
    )

    return logger
