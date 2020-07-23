import logging
from configparser import ConfigParser

from telegram.ext import Filters, MessageHandler, Updater

_logger = logging.getLogger(__name__)


class Broker:
    def __init__(self, config_path=False, **kwargs):
        if config_path:
            self.parser = ConfigParser()
            self.parser.read(config_path)
            self.token = self.parser.get("telegram", "token")
        else:
            self.token = kwargs.get("token")

        self.updater = Updater(self.token, use_context=True)
        self.dp = self.updater.dispatcher

    def message_callback(self, update, context):
        raise Exception

    def error_handler(self, update, context):
        update.message.reply_text(
            "Sorry, we couldn't process your message, resend it later"
        )

    def _add_handlers(self):
        self.dp.add_handler(MessageHandler(Filters.all, self.message_callback))
        self.dp.add_error_handler(self.error_handler)

    def run(self):
        _logger.info("Initializing Telegram broker")

        self._add_handlers()
        self.updater.start_polling()
        self.updater.idle()
        _logger.info("Closing Telegram broker")
