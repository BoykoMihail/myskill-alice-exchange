# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import json
import logging
import re
from sys import path
from decimal import Decimal
from configparser import ConfigParser

from mdapi import DataStorage, MDApiConnector
from fundamental import FundamentalApi

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# read config
config = ConfigParser()
config.read_file(open('config.ini'))

# create connectors to API
api = MDApiConnector(
    client_id=config['API']['client_id'],
    app_id=config['API']['app_id'],
    key=config['API']['shared_key']
)

fapi = FundamentalApi()

storage = DataStorage(api)
storage.start()

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request
app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.
sessionStorage = {}

# Задаем параметры приложения Flask.
@app.route("/", methods=['POST'])

def main():
    
# Функция получает тело запроса и возвращает ответ.
    logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )

# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
        }

        res['response']['text'] = 'Привет! Купи слона!'
        res['response']['buttons'] = get_suggests(user_id)
        return

    # Обрабатываем ответ пользователя.
    if req['request']['original_utterance'].lower() in [
        'ладно',
        'куплю',
        'покупаю',
        'хорошо',
    ]:
        # Пользователь согласился, прощаемся.
        res['response']['text'] = 'Слона можно найти на Яндекс.Маркете!'
        return

    # Если нет, то убеждаем его купить слона!
    res['response']['text'] = 'Все говорят "%s", а ты купи слона!' % (
        req['request']['original_utterance']
    )
    res['response']['buttons'] = get_suggests(user_id)

# Функция возвращает две подсказки для ответа.
def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": "https://market.yandex.ru/search?text=слон",
            "hide": True
        })

    return suggests
    
# Welcome message
def start(bot, update):
    msg = "Привет, {user_name}! \n\n" + \
    "Меня можно спросить об акциях фондового рынка США \n" + \
    "и я покажу их оценку P/E и текущую цену. \n\n" + \
    "Например: расскажи об AAPL или NVDA"

    # Send the message
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg.format(
                         user_name=update.message.from_user.first_name,
                         bot_name=bot.name))

@run_async
def process(bot, update):
    if update.message.text.find("брокера посоветуешь") > 0:
        update.message.reply_text("Лично я рекомендую EXANTE!")
        return

    tickers = re.findall(r'[A-Z]{1,4}', update.message.text)

    msg = ""
    for ticker in tickers:
        stock = storage.stocks.get(ticker)
        if not stock: continue

        eps = fapi.request(ticker).get('EarningsShare')
        if not eps:
            logger.warning("Can't fetch EPS for {}".format(ticker))
            continue

        price = api.get_last_ohlc_bar(stock['id'])
        ratio = Decimal("%.4f" % price['close']) / Decimal(eps)

        msg += "{ticker} ({name}, {exchange}): EPS {eps}, P/E {ratio}, цена ${price} \n".format(
            ticker = ticker,
            name = stock['description'],
            exchange = stock['exchange'],
            ratio = "%.2f" % ratio,
            price = price['close'],
            eps = eps
        )

    if not msg:
        msg = "Не удалось получить данные по тикерам из запроса :(\n" +\
              "Попробуйте спросить о чем-то популярном, вроде GOOG или AAPL."

    bot.send_message(chat_id=update.message.chat_id, text=msg)
