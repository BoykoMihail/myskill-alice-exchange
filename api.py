# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import re
import json
import logging
import yfinance as yf
from yahoo_finance import Share

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
        msg = "Привет! \n\n" + \
        "Меня можно спросить об акциях фондового рынка США \n" + \
        "и я покажу их оценку P/E и текущую цену. \n\n" + \
        "Например: расскажи об AAPL или NVDA aa"

        res['response']['text'] = msg
        return
        
    tickers = re.findall(r'[A-Z]{1,4}', req['request']['original_utterance'])
    msg = req['request']['original_utterance'] + " "
#    for ticker in tickers:
##        yahoo = Share(ticker)
##        sys.stdout.write("Hello " + yahoo.get_open())
#        msg += yahoo.get_open()
        
    res['response']['text'] = msg
    return
#        stock = storage.stocks.get(ticker)
#        if not stock: continue
#
#        eps = fapi.request(ticker).get('EarningsShare')
#        if not eps:
#            logger.warning("Can't fetch EPS for {}".format(ticker))
#            continue
#
#        price = api.get_last_ohlc_bar(stock['id'])
#        ratio = Decimal("%.4f" % price['close']) / Decimal(eps)
#
#        msg += "{ticker} ({name}, {exchange}): EPS {eps}, P/E {ratio}, цена ${price} \n".format(
#            ticker = ticker,
#            name = stock['description'],
#            exchange = stock['exchange'],
#            ratio = "%.2f" % ratio,
#            price = price['close'],
#            eps = eps
#        )

#    # Обрабатываем ответ пользователя.
#    if req['request']['original_utterance'].lower() in [
#        'ладно',
#        'куплю',
#        'покупаю',
#        'хорошо',
#    ]:
#        # Пользователь согласился, прощаемся.
#        res['response']['text'] = 'Слона можно найти на Яндекс.Маркете!'
#        return

    # Если нет, то убеждаем его купить слона!

#    msft = yf.Ticker("MSFT")
#
#    # get stock info
#    ttt = msft.info
#    text = ""
#    for t in ttt:
#        text += t

#    'Все говорят "%s", а ты купи слона!' + text % (
#        req['request']['original_utterance']
#    )
#    res['response']['buttons'] = get_suggests(user_id)

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
