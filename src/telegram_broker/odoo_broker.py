import base64
import logging
import mimetypes
import traceback
from io import BytesIO, StringIO
from xmlrpc.client import ServerProxy

import magic
import telegram
from lottie.exporters import exporters
from lottie.importers import importers

from .broker import Broker

mimetypes.add_type("image/webp", ".webp")

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

    def message_callback_message(self, chat_id, date, body, message_id, attachments):
        return self.process_odoo(
            "mail.telegram.chat",
            "telegram_message_post_broker",
            [chat_id],
            date=date,
            body=body,
            message_id=message_id,
            subtype="mt_comment",
            attachments=attachments,
            context={"notify_telegram": True},
        )

    def _sticker_input_options(self):
        return {}

    def _sticker_output_options(self):
        return {}

    def _get_attachment_name(self, attachment):
        if hasattr(attachment, "title"):
            if attachment.title:
                return attachment.title
        if hasattr(attachment, "file_name"):
            if attachment.file_name:
                return attachment.file_name
        if isinstance(attachment, telegram.Sticker):
            return attachment.set_name or attachment.emoji or "sticker"
        if isinstance(attachment, telegram.Contact):
            return attachment.first_name
        return attachment.file_id

    def process_file(self, attachment):
        if isinstance(
            attachment,
            (
                telegram.Game,
                telegram.Invoice,
                telegram.Location,
                telegram.SuccessfulPayment,
                telegram.Venue,
            ),
        ):
            return
        if isinstance(attachment, telegram.Contact):
            data = attachment.vcard.encode("utf-8")
        else:
            data = bytes(attachment.get_file().download_as_bytearray())
        file_name = self._get_attachment_name(attachment)
        if isinstance(attachment, telegram.Sticker):
            suf = "tgs"
            for p in importers:
                if suf in p.extensions:
                    importer = p
                    break
            exporter = exporters.get("gif")
            inpt = BytesIO(data)
            an = importer.process(inpt, **self._sticker_input_options())
            output_options = self._sticker_output_options()
            fps = output_options.pop("fps", False)
            if fps:
                an.frame_rate = fps
            output = BytesIO()
            exporter.process(an, output, **output_options)
            data = output.getvalue()
        mimetype = magic.from_buffer(data, mime=True)
        return (
            "{}{}".format(file_name, mimetypes.guess_extension(mimetype)),
            base64.b64encode(data).decode("utf-8"),
            mimetype,
        )

    def message_callback(self, update, context):
        _logger.debug("Calling message %s" % update)
        try:
            chat_id = self._get_chat(update, context)
            if not chat_id:
                return
            if update.message:

                body = ""
                attachments = []
                if update.message.text_html:
                    body = update.message.text_html
                if update.message.effective_attachment:
                    effective_attachment = update.message.effective_attachment
                    if isinstance(effective_attachment, list):
                        effective_attachment = effective_attachment[0]
                    if isinstance(effective_attachment, telegram.Location):
                        body += (
                            '<a target="_blank" href="https://www.google.com/'
                            'maps/search/?api=1&query=%s,%s">Location</a>'
                            % (
                                effective_attachment.latitude,
                                effective_attachment.longitude,
                            )
                        )
                    attachment_data = self.process_file(effective_attachment)
                    if attachment_data:
                        attachments.append(attachment_data)
                if len(body) > 0 or attachments:
                    return self.message_callback_message(
                        chat_id,
                        update.message.date,
                        body,
                        update.message.message_id,
                        attachments,
                    )
            return super().message_callback(update, context)
        except Exception:
            buff = StringIO()
            traceback.print_exc(file=buff)
            error = buff.getvalue()
            _logger.warning(error)
            raise
