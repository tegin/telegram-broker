import logging
import traceback
from io import StringIO
from xmlrpc.client import ServerProxy

from .broker import Broker

_logger = logging.getLogger(__name__)


class OdooBroker(Broker):
    def __init__(self, config_path=False, **kwargs):
        super(OdooBroker, self).__init__(config_path=config_path, **kwargs)
        if self.parser:
            self._url = self.parser.get("odoo", "url")
            self._db = self.parser.get("odoo", "db")
            self._username = self.parser.get("odoo", "username")
            self._password = self.parser.get("odoo", "password")
        else:
            self._url = kwargs.get("url")
            self._db = kwargs.get("db")
            self._username = kwargs.get("username")
            self._password = kwargs.get("password")
        self.common = ServerProxy("{}/xmlrpc/2/common".format(self._url))
        self._uid = self.common.authenticate(
            self._db, self._username, self._password, {}
        )
        self.models = ServerProxy("{}/xmlrpc/2/object".format(self._url))
        self.bot_id = self.process_odoo(
            "mail.telegram.bot", "search", [("token", "=", self.token)]
        )[0]

    def process_odoo(self, model, function, *args, **kwargs):
        return self.models.execute_kw(
            self._db, self._uid, self._password, model, function, args, kwargs
        )

    def _get_chat(self, update, context):
        chat = self.process_odoo(
            "mail.telegram.chat",
            "search",
            [("chat_id", "=", update._effective_chat.id), ("bot_id", "=", self.bot_id)],
        )
        if chat:
            chat = chat[0]
        else:
            names = [
                update._effective_chat.first_name,
                update._effective_chat.last_name,
                update._effective_chat.description,
                update._effective_chat.title,
            ]
            chat = self.process_odoo(
                "mail.telegram.chat",
                "create",
                {
                    "chat_id": update.message.chat_id,
                    "bot_id": self.bot_id,
                    "name": " ".join([n for n in names if n]),
                    "show_on_app": True,
                },
            )
        return chat

    def message_callback_message(self, chat_id, date, body, message_id):
        try:
            return self.process_odoo(
                "mail.telegram.chat",
                "telegram_message_post_broker",
                [chat_id],
                date=date,
                body=body,
                message_id=message_id,
                subtype="mt_comment",
                context={"notify_telegram": True},
            )
        except Exception:
            buff = StringIO()
            traceback.print_exc(file=buff)
            error = buff.getvalue()
            _logger.warning(error)
            raise

    def message_callback(self, update, context):
        _logger.debug("Calling message %s" % update)
        chat_id = self._get_chat(self, update, context)
        if not chat_id:
            return
        if update.message:
            return self.message_callback_message(
                chat_id,
                update.message.date,
                update.message.text_html,
                update.message.message_id,
            )
        return super().message_callback(update, context)