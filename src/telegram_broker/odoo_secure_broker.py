import logging
import traceback
from io import StringIO

from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters

from .odoo_broker import OdooBroker

_logger = logging.getLogger(__name__)


class OdooSecureBroker(OdooBroker):
    def __init__(self, config_path=False, **kwargs):
        super().__init__(config_path=config_path, **kwargs)
        self._chats = {}
        for data in self.process_odoo(
            "mail.telegram.chat",
            "search_read",
            [("bot_id", "=", self.bot_id)],
            ["chat_id"],
        ):
            self._chats[int(data["chat_id"])] = data["id"]
        if self.parser:
            self.secure_key = self.parser.get("telegram", "password")
        else:
            self.secure_key = kwargs.get("telegram_password")

    def _get_chat_name(self, update, context):
        names = [
            update._effective_chat.first_name,
            update._effective_chat.last_name,
            update._effective_chat.description,
            update._effective_chat.title,
        ]
        return " ".join([n for n in names if n])

    def _start_chat_handler(self, update, context):
        _logger.info(
            "Not Secure Chat from %s - %s"
            % (update._effective_chat.chat_id, self._get_chat_name(update, context))
        )

    def _start_chat_handler_secure(self, update, context):
        _logger.info("Creating chat")
        try:
            if self._chats.get(update._effective_chat.id, False):
                return

            self._chats[update._effective_chat.id] = self.process_odoo(
                "mail.telegram.chat",
                "create",
                {
                    "chat_id": update._effective_chat.id,
                    "bot_id": self.bot_id,
                    "name": self._get_chat_name(update, context),
                    "show_on_app": True,
                },
            )
            return self.message_callback_message(
                self._get_chat(update, context),
                update.message.date,
                "start",
                update.message.message_id,
            )
        except Exception:
            buff = StringIO()
            traceback.print_exc(file=buff)
            error = buff.getvalue()
            _logger.warning(error)
            raise

    def _add_handlers(self):
        self.dp.add_handler(
            CommandHandler(
                "start", self._start_chat_handler_secure, Filters.regex(self.secure_key)
            )
        )
        self.dp.add_handler(CommandHandler("start", self._start_chat_handler))
        super()._add_handlers()

    def _get_chat(self, update, context):
        return self._chats.get(update._effective_chat.id, False)
