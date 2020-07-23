import logging.config
import os

from telegram_broker import OdooSecureBroker as Broker

path = os.path.dirname(os.path.realpath(__file__))
log_folder = path + "/log"
if not os.path.isdir(log_folder):
    os.mkdir(log_folder)
logging.config.fileConfig(path + "/telegram.logging.conf")
Broker(
    token="YOUR_TOKEN",
    db="YOUR_DB",
    url="YOUR_URL",
    username="YOUR USER",
    password="YOUR PASSWORD",
    telegram_password="TELEGRAM_PASSWORD",
).run()
