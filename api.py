# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import re
import json
from yahoo_fin import stock_info as si
import requests
import random
import string

import firebase_admin
from firebase_admin import credentials, firestore
import yfinance as yf
import wikipedia
from googletrans import Translator
from names_translator import Transliterator
import difflib
import itertools
from math import modf
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
    
def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
    
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
            
def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
        
def listToString(s,t):
    str1 = ""
    for ele in s:
        str1 += ele
        str1 += t
    return str1[:-1]
    
def getTickers(text):
    tickers = re.findall(r'[A-Z]{1,4}', text)
    tr = Transliterator()
    textCurrent = text
    textCurrent = textCurrent.replace(',', ' ')
    textCurrent = textCurrent.replace('.', '')
    textArray = textCurrent.split(' ')
    textTranslate = []
    temp = []
    
    for t in textArray:
        translate = ""
        for val in tr.transliterate(t, "", ""):
            if isEnglish(val):
                translate = val
                break
        textTranslate.append(translate)
        temp.append(translate)
    

    if len(temp) > 2:
        for item in itertools.combinations(temp, 3):
            textTranslate.append(' '.join(item))
            textTranslate.append('-'.join(item))
    if len(temp) > 1:
        for item in itertools.combinations(temp, 2):
            textTranslate.append(' '.join(item))
            textTranslate.append('-'.join(item))
    
    cred = credentials.Certificate("serviceAccountKey.json")
    firebaseApp = firebase_admin.initialize_app(cred)
    datab = firestore.client()

    try:

        usersref = datab.collection(u'tickers')
        docs = usersref.stream()
        
        tickerCompanyName = []
        tickerName = []
        tickerNameMap = {}
        for doc in docs:
            tickerCompanyName.append(doc.to_dict()['EnglishName'])
            tickerNameMap[doc.to_dict()['EnglishName']] = doc.to_dict()['Ticker']
        
        realNames = []
        for t in textTranslate:
            findName = difflib.get_close_matches(t, tickerCompanyName)
            if len(findName) > 0:
                if tickerNameMap[findName[0]] not in tickers :
                    tickers.append(tickerNameMap[findName[0]])

        firebase_admin.delete_app(firebaseApp)
        
        return tickers


    except Exception as e:
        firebase_admin.delete_app(firebaseApp)
        print(e)
        print(u'No such document!')
        return []
        
def getCompaniInfo(tickers):
    result = ""
    translator = Translator()
    for tic in tickers:
        wikipedia.set_lang("ru")
        name = get_symbol(tic)
        info = wikipedia.summary(name, sentences=2)
        name = name.split(' ')[0].replace(',', '').replace('.','')
        links = wikipedia.WikipediaPage(name.split(' ')[0])
#        msft = yf.Ticker(tic)
#        info = str(msft.get_info()['longBusinessSummary'])
#        translations = translator.translate(info, dest='ru')
        result = result + info + "..."
        url = 'https://ru.wikipedia.org/wiki/{}'.format(name)
    return result, url, name
    
#        for te in translations.text.split('. ')[:1]:
#            result = result + te
#    return result + "..."
#    расскажи о MSFT

def get_suggests(name, url):
    
    suggests = [
        { "title": "Перейти на сайт {}".format(name),
        "url": url,
        "hide": True
    }]

    return suggests
    
            
# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        
        msg = " Привет! \n\n" + \
        "Меня можно спросить об акциях фондового рынка США \n" + \
        "Например: расскажи об AAPL или NVDA"

        res['response']['text'] = msg
        return
    
    listHelp = ["ПОМОЩЬ", "ЧТО ТЫ УМЕЕШЬ?", "ЧТО ТЫ УМЕЕШЬ", "ЧТО УМЕЕШЬ", "ЧТО УМЕЕШЬ?"]
    listAbout = "РАССКАЖИ О"
    
    if req['request']['original_utterance'].upper() in listHelp:
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        res['response']['text'] = msg
        return
        
    if req['request']['original_utterance'].upper().find(listAbout) != -1:

        text = req['request']['original_utterance']
        text = text.replace(listAbout, "")
        tickers = getTickers(text)
        msg, url, name = getCompaniInfo(tickers)
        if msg == "":
            msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
            res['response']['text'] = msg
        else:
            res['response']['text'] = msg
            res['response']['buttons'] = get_suggests(name, url)
        return
    
    tickers = getTickers(req['request']['original_utterance'])

    msg = ""
    if len(tickers) == 0:
        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
    else:
        msg = ""
        for ticker in tickers:
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

if __name__ == "__main__":
    text = "расскажи о тесла"
    listHelp = ["ПОМОЩЬ", "ЧТО ТЫ УМЕЕШЬ?", "ЧТО ТЫ УМЕЕШЬ", "ЧТО УМЕЕШЬ", "ЧТО УМЕЕШЬ?"]
    listAbout = "РАССКАЖИ О"

    if text.upper() in listHelp:
        # Помощь

        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        print(msg)

    if text.upper().find(listAbout) != -1:
        user_id = 1
        texst = text
        texst = texst.replace(listAbout, "")
        tickers = getTickers(texst)
        msg, url, name = getCompaniInfo(tickers)
        if msg == "":
            msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
            print(msg)
        else:
            print(msg + "12")
            print(get_suggests(name, url))

    tickers = getTickers(text)

    msg = ""
    if len(tickers) == 0:
        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
    else:
        msg = ""
        for ticker in tickers:
            name = get_symbol(ticker)
            price = str(si.get_live_price(ticker))
            ex_desc = get_exchDisp(ticker)
            msg += "{ticker} ({name}, {exchange}): цена ${price} \n".format(
                ticker = ticker,
                name = name,
                exchange = ex_desc,
                price = price
            )

    print(msg)
    

