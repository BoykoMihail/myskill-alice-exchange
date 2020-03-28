# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import re
import json
from yahoo_fin import stock_info as si
import requests

import firebase_admin
from firebase_admin import credentials, firestore
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

def get_symbol(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)

    result = requests.get(url).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']
            
def get_exchDisp(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)

    result = requests.get(url).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['exchDisp']
            
# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        
        msg = " Привет! \n\n" + \
        "Меня можно спросить об акциях фондового рынка США \n" + \
        "Например: расскажи об AAPL или NVDA"
        
        # TO DO

        cred = credentials.Certificate("/Users/mikhailboyko/myskill-alice/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
                
        datab = firestore.client()
        usersref = datab.collection(u'tickers')
        docs = usersref.stream()
        
        for doc in docs:
            msg = msg + '{} : {}'.format(doc.id,doc.to_dict())

        res['response']['text'] = msg
        return
        
    if req['request']['original_utterance'].upper() == "ПОМОЩЬ":
        # Помощь
        
        msg = "Меня можно спросить об акциях фондового рынка США \n" + \
            "Например: расскажи об AAPL или NVDA"

        res['response']['text'] = msg
        return
        
    if req['request']['original_utterance'].upper() == "ЧТО ТЫ УМЕЕШЬ?":
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        res['response']['text'] = msg
        return
        
    if req['request']['original_utterance'].upper() == "ЧТО ТЫ УМЕЕШЬ":
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        res['response']['text'] = msg
        return
        
    if req['request']['original_utterance'].upper() == "ЧТО УМЕЕШЬ":
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        res['response']['text'] = msg
        return
        
    if req['request']['original_utterance'].upper() == "ЧТО УМЕЕШЬ?":
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        res['response']['text'] = msg
        return
        
    
        
    tickers = re.findall(r'[A-Z]{1,4}', req['request']['original_utterance'])
    msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
    
    for ticker in tickers:
        msg = ""
        name = get_symbol(ticker)
        price = str(si.get_live_price(ticker))
        ex_desc = get_exchDisp(ticker)
        msg += "{ticker} ({name}, {exchange}): цена ${price} \n".format(
            ticker = ticker,
            name = name,
            exchange = ex_desc,
            price = price
        )
        
    res['response']['text'] = msg
    return

