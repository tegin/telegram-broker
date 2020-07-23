import logging.config
import os

from telegram_broker import OdooSecureBroker as Broker

path = os.path.dirname(os.path.realpath(__file__))
log_folder = path + "/log"
if not os.path.isdir(log_folder):
    os.mkdir(log_folder)
logging.config.fileConfig(path + "/telegram.logging.conf")
Broker(path + "/broker.conf").run()
