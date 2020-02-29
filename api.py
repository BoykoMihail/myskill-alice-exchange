# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import re
import json
from yahoo_fin import stock_info as si

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request
app = Flask(__name__)

# Задаем параметры приложения Flask.
@app.route("/", methods=['POST'])

def main():

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

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
        "Например: расскажи об AAPL или NVDA"

        res['response']['text'] = msg
        return
        
    tickers = re.findall(r'[A-Z]{1,4}', req['request']['original_utterance'])
    msg = req['request']['original_utterance'] + " "
    
    for ticker in tickers:
        msg += str(si.get_live_price(ticker))
        
    res['response']['text'] = msg
    return

