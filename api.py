# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import re
import json
from yahoo_fin import stock_info as si
import requests
import string

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import wikipedia
from names_translator import Transliterator
import difflib
import itertools
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

def removeVowels(string):
    newstr = string.upper();
    vowels = ('A', 'E', 'I', 'O', 'U','Y');
    for x in string:
        if x in vowels:
            newstr = newstr.replace(x,"");
    return newstr;
    
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
    tickers = []
    print(text)
    tr = Transliterator()
    textCurrent = text
    textArray = textCurrent.split(' ')
    textTranslate = []
    temp = []
    
    for t in textArray:
        translate = ""
        for val in tr.transliterate(t, "", ""):
            if isEnglish(val):
                if len(val) > 3:
                    translate = val
                    textTranslate.append(translate)
                    temp.append(translate)
        
    if len(temp) > 2:
        for item in itertools.combinations(temp, 3):
            textTranslate.append(' '.join(item))
            
    cred = credentials.Certificate('serviceAccountKey.json')
    # Initialize the app with a service account, granting admin privileges
    firebaseApp = firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://boyko-quotes.firebaseio.com/'
    })
    
    ref = db.reference('-M5Bp33uufz6f2ayRMuB')
    arr = ref.get()

    try:
    
        tickerCompanyName = []
        tickerCompanyNameSplit = []
        tickerName = []
        tickerNameMap = {}
        tickerNameMapRevert = {}
        tickerNameMapSplit = {}
        for doc in arr:
            docc = doc['Name'].upper()
            tickerCompanyName.append(docc)
            tkr = doc['Symbol']
            tickerName.append(tkr)
            tickerNameMap[docc] = tkr
            tickerNameMapRevert[tkr] = docc
        
        realNames = []
        for t in textTranslate:
            findName = difflib.get_close_matches(t, tickerCompanyName)
            if len(findName) > 0:
                if findName[0] not in realNames :
                    realNames.append(findName[0])
        if len(realNames) > 0:
            arr = [0] * len(realNames)
            for t in textTranslate:
                temp = difflib.get_close_matches(t, realNames)
                if len(temp) > 0:
                    arr[realNames.index(temp[0])] += 1
                    
            tickers.append(tickerNameMap[realNames[arr.index(max(arr))]])
            
        else:
            for t in textTranslate:
                findName = difflib.get_close_matches(removeVowels(t), tickerName)
                if len(findName) > 0:
                    if findName[0] not in tickers :
                        tickers.append(findName[0])
                        
        
        
        firebase_admin.delete_app(firebaseApp)
        
        return tickerNameMapRevert, tickers


    except Exception as e:
        firebase_admin.delete_app(firebaseApp)
        print(e)
        print(u'No such document!')
        return []
        
def getCompaniInfo(tickers):
    result = ""
    url = ""
    name = ""
    for tic in tickers:
        wikipedia.set_lang("en")
        name = get_symbol(tic)
        try:
            info = wikipedia.summary(name, sentences=2)
            links = wikipedia.WikipediaPage(name.split(' ')[0])
            result = result + info + "..."
            url = 'https://ru.wikipedia.org/wiki/{}'.format(name)
            return result, url, name
        except Exception as e:
            return "К сожалению по компании {} Ничего не найдено :(".format(name), "", ""
    

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
    textForm = req['request']['original_utterance'].upper()
#    textForm = req['request']['original_utterance'].upper().replace(",", "").replace(" и ", " ").replace("пожалуйста", "").replace("например о", "").replace("чтото о" , "").replace("что-то о" , "").replace("расскажи о" , "").replace("расскажи о" , "").lstrip()
    
    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        
        msg = " Привет! \n\n" + \
        "Меня можно спросить об акциях фондового рынка США \n" + \
        "Например: расскажи об AAPL или NVDA"

        res['response']['text'] = msg
        return
    
    listHelp = ["ПОМОЩЬ", "ЧТО ТЫ УМЕЕШЬ?", "ЧТО ТЫ УМЕЕШЬ", "ЧТО УМЕЕШЬ", "ЧТО УМЕЕШЬ?"]
    listAbout = "ВИКИ О"
    
    if textForm in listHelp:
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672\n" + \
            "Или можешь спросить у меня иноврмацию о компании!" + \
            "Например Ты можешь сказать: Вики о AAPL"

        res['response']['text'] = msg
        return
        
    if textForm.find(listAbout) != -1:
        text = textForm
        text = text.replace(listAbout, "").lstrip()
        tickers = getTickers(text)
        msg, url, name = getCompaniInfo(tickers)
        if url == "":
            res['response']['text'] = msg
        else:
            res['response']['text'] = msg
            res['response']['buttons'] = get_suggests(name, url)
        return
    
    tickerNameMap, tickers = getTickers(textForm)
    
    msg = ""
    if len(tickers) == 0:
        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
    else:
        msg = ""
        for ticker in tickers:
            name = tickerNameMap[ticker]
            try:
                price = str(si.get_live_price(ticker))
#                ex_desc = get_exchDisp(ticker)
                msg += "{ticker} ({name}): цена ${price} \n".format(
                    ticker = ticker,
                    name = name,
                    price = price
                )
            except Exception as e:
                print(e)
        
    res['response']['text'] = msg
    
    return

if __name__ == "__main__":
#//Trevena
    text = "Applied Genetic".upper().lstrip()
    listHelp = ["ПОМОЩЬ", "ЧТО ТЫ УМЕЕШЬ?", "ЧТО ТЫ УМЕЕШЬ", "ЧТО УМЕЕШЬ", "ЧТО УМЕЕШЬ?"]
    listAbout = "ВИКИ О"

    if text.upper() in listHelp:
        # Помощь

        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672"

        print(msg)
        
    if text.upper().find(listAbout) != -1:
        user_id = 1
        texst = text
        texst = texst.upper().replace(listAbout, "").lstrip()
        tickers = getTickers(texst)
        msg, url, name = getCompaniInfo(tickers)
        if url == "":
            print(msg)
        else:
            print(msg + "12")
            print(get_suggests(name, url))

    aaa, tickers = getTickers(text)
    print("tickers:")
    print(tickers)
    print("----------")
    msg = ""
    if len(tickers) == 0:
        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
    else:
        msg = ""
        for ticker in tickers:
            try:
                name = aaa[ticker]
                price = str(si.get_live_price(ticker))
                ex_desc = get_exchDisp(ticker)
                msg += "{ticker} ({name}, {exchange}): цена ${price} \n".format(
                    ticker = ticker,
                    name = name,
                    exchange = ex_desc,
                    price = price
                )
            except Exception as e:
                print( e)

    print(msg)
    

