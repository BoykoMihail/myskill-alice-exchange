# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import re
import json
from yahoo_fin import stock_info as si
import requests
import string
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import wikipedia
from names_translator import Transliterator
import difflib
import itertools
import threading
import time
import concurrent.futures
import numpy

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

def thread_function():
    cred = credentials.Certificate('serviceAccountKey.json')
    # Initialize the app with a service account, granting admin privileges
    firebaseApp = firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://boyko-quotes.firebaseio.com/'
    })

    ref = db.reference('-M6W9myLcSdr3sibu1-8')
    arr = ref.get()


    with open('data.txt', 'w') as outfile:
        json.dump(arr, outfile)

    firebase_admin.delete_app(firebaseApp)
    
    print("thread_function is ok!")

def thread_function_parse_All(count, tickerCompanyName, tickerName, tickerNameMap, textTranslate):
    tickers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
        for l1 in range(count):
            future = executor.submit(thread_function_parse, tickerCompanyName, tickerName, tickerNameMap,textTranslate[l1])
            return_value = future.result()
            if len(future.result()) > 0:
                tickers.extend(return_value)
    return tickers
    
def thread_function_parse(tickerCompanyName, tickerName, tickerNameMap, textTranslate):
    tickers = []
            
    if len(tickers) == 0:
        realNames = []
        
        for t in textTranslate:
            findName = difflib.get_close_matches(t, tickerCompanyName)
            for fname in findName:
                if fname not in realNames :
                    realNames.append(fname)
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
                for fname in findName:
                    if fname not in tickers :
                        tickers.append(fname)
    return tickers
            
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
            
def get_price_by(tic, count):
    data = si.get_data(tic , start_date = (datetime.today() - timedelta(days=count)).strftime('%m/%d/%Y') , end_date = datetime.today().strftime('%m/%d/%Y'))
    strr = ""
    for index, row in data.iterrows():
        strr += str(row[1]) + "\n"
    return strr
            
def most_frequent(List):
    counter = 0
    num = List[0]
        
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i

    return num
            
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
    tr = Transliterator()
    textCurrent = text
    textArray = text.split(' ')
#    textArray.append(text)
    textTranslate = []
    temp = []
    
    for t in textArray:
        translate = ""
        if isEnglish(t):
            translate = t.upper()
            textTranslate.append(translate)
            temp.append(translate)
        else:
            for val in tr.transliterate(t, "", ""):
                if isEnglish(val):
                    if len(val) > 3 and val.upper() not in textTranslate:
                        translate = val.upper()
                        textTranslate.append(translate)
                        temp.append(translate)
    for val in tr.transliterate(text, "", ""):
        if isEnglish(val):
            if len(val) > 3 and val.upper() not in textTranslate:
                translate = val.upper()
                textTranslate.append(translate)
                temp.append(translate)
    
    
#    if len(temp) > 2:
#        for item in itertools.combinations(temp, 3):
#            textTranslate.append(' '.join(item))
    if len(temp) > 1:
        for item in itertools.combinations(temp, 2):
            textTranslate.append(' '.join(item))
            
    arr = ""
    with open('data.txt') as json_file:
        arr = json.load(json_file)
        
    
    
#    start = time.time()
#    tickerCompanyName = []
#    tickerCompanyNameSplit = []
#    tickerName = []
#    tickerNameMap = {}
#    tickerStatMap = {}
#    tickerNameMapRevert = {}
#    for doc in arr:
#        doccName = doc['Name'].replace(" Co", "").strip()
#        tickerCompanyName.append(doccName)
#        tkr = doc['Symbol']
#        tickerName.append(tkr)
#        tickerNameMap[doccName] = tkr
#        tickerNameMapRevert[tkr] = doccName
#        stat = doc['Stat']
##            re.sub(r'\([^()]*\)', '', doc['Stat'].replace("=", "").replace("  ", " "))
#        tickerStatMap[tkr] = stat[:900] + "..."
#    count = 8
#    textTranslate_split = numpy.array_split(numpy.array(textTranslate),count)
##
#    tickers = thread_function_parse_All(count, tickerCompanyName, tickerName, tickerNameMap, textTranslate_split)
#    tick = ""
#    if len(tickers) > 1:
#        tick = [most_frequent(tickers)]
#    else:
#        tick = tickers
#    return tickerStatMap, tickerNameMapRevert, tick
#    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
#        for str in textTranslate:
#            future = executor.submit(thread_function_parse_All, tickerCompanyName_split, tickerName_split, tickerNameMap, textTranslate_split)
#            return_value = future.result()
#            if len(return_value) > 0:
#                tickers.extend(return_value)
#    print(tickers)
#    print("With ",14," threads: ", time.time() - start)
#
    try:
        tickers = []
        start = time.time()
        tickerCompanyName = []
        tickerCompanyNameSplit = []
        tickerName = []
        tickerNameMap = {}
        tickerStatMap = {}
        tickerNameMapRevert = {}
        for doc in arr:
            doccName = doc['Name'].replace(" Co", "").strip()
            tickerCompanyName.append(doccName)
            tkr = doc['Symbol']
            tickerName.append(tkr)
            tickerNameMap[doccName] = tkr
            tickerNameMapRevert[tkr] = doccName
            stat = doc['Stat']
#            re.sub(r'\([^()]*\)', '', doc['Stat'].replace("=", "").replace("  ", " "))
            tickerStatMap[tkr] = stat[:900] + "..."
            for t in textTranslate:
                if set(t.split(' ' )).issubset(set(doccName.split(' ' ))):
#                    if tkr not in tickers:
                    tickers.append(tkr)
        if len(tickers) == 0:
            realNames = []

            for t in textTranslate:
                findName = difflib.get_close_matches(t, tickerCompanyName)
                for fname in findName:
                    if fname not in realNames :
                        realNames.append(fname)
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
                    for fname in findName:
                        if fname not in tickers :
                            tickers.append(fname)

#        firebase_admin.delete_app(firebaseApp)
        tick = ""
        if len(tickers) > 1:
            tick = [most_frequent(tickers)]
        else:
            tick = tickers
        print("Without threads: ",time.time() - start)
        return tickerStatMap, tickerNameMapRevert, tick


    except Exception as e:
#        firebase_admin.delete_app(firebaseApp)
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
    
def getMsg_by_interval(textForm, count):
    text = textForm
    _, tickerNameMap, tickers = getTickers(text)
    msg = ""
    if len(tickers) == 0:
        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
    else:
        msg = ""
        strangTickermsg = ""
        for ticker in tickers:
            name = tickerNameMap[ticker]
            try:

                strangTickermsg = "Цена за последние 7 дней {ticker}:{name}".format(
                    ticker = ticker,
                    name = name
                )
                msg += "{ticker} ({name}): \n".format(
                    ticker = ticker,
                    name = name
                )
                pr_week = get_price_by(ticker, count)
                msg += pr_week
            except Exception as e:
                print(e)
    
    if msg == "":
        msg = "Извините, по этим компаниям мы не смогли узнать цену. Попробуйте еще раз!\n" + strangTickermsg
    
    return msg
            
# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):

    x = threading.Thread(target=thread_function, args=())
    x.start()
    
    user_id = req['session']['user_id']
#    textForm = req['request']['original_utterance'].upper()
    textForm = req['request']['original_utterance'].upper().replace(",", "").replace(" и ", " ").replace("пожалуйста", "").replace("например о", "").replace("чтото о" , "").replace("что-то о" , "").replace("расскажи о" , "").replace("расскажи о" , "").replace("-","").replace("INC.", "").replace("GROUP", "").replace("CORPORATION", "").lstrip()
    
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
    listWeek= ["ЗА НЕДЕЛЮ О","ЗА НЕДЕЛЮ"]
    listWeek2= ["ЗА ДВЕ НЕДЕЛИ О","ЗА ДВЕ НЕДЕЛИ","ЗА 2 НЕДЕЛИ О","ЗА 2 НЕДЕЛИ"]
    listWeek3= ["ЗА ТРИ НЕДЕЛИ О","ЗА ТРИ НЕДЕЛИ","ЗА 3 НЕДЕЛИ О","ЗА 3 НЕДЕЛИ"]
    listWeek4= ["ЗА МЕСЯЦ О","ЗА МЕСЯЦ"]
    
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
    
    isFound = False
    isFound2 = False
    isFound3 = False
    isFound4 = False
    for i in listWeek:
        if textForm.find(i) != -1:
            isFound = True
            break
            
    if isFound:
        
        for l in listWeek:
            textForm = textForm.replace(l, "").lstrip()
        msg = getMsg_by_interval(textForm, 7)
        res['response']['text'] = msg
        return
    else:
#        isFound2 = False
        for i in listWeek2:
            if textForm.find(i) != -1:
                isFound2 = True
                break
        if isFound2:

           for l in listWeek2:
              textForm = textForm.replace(l, "").lstrip()
           msg = getMsg_by_interval(textForm, 14)
           res['response']['text'] = msg
           return
        else:
            isFound3 = False
            for i in listWeek3:
                if textForm.find(i) != -1:
                    isFound3 = True
                    break
            if isFound3:

               for l in listWeek3:
                  textForm = textForm.replace(l, "").lstrip()
               msg = getMsg_by_interval(textForm, 21)
               res['response']['text'] = msg
               return
            else:
                isFound4 = False
                for i in listWeek4:
                    if textForm.find(i) != -1:
                        isFound4 = True
                        break
                if isFound4:

                   for l in listWeek4:
                      textForm = textForm.replace(l, "").lstrip()
                   msg = getMsg_by_interval(textForm, 31)
                   res['response']['text'] = msg
                   return
                else:
                
                    tickerStatMap, tickerNameMap, tickers = getTickers(textForm)
                    msg = ""
                    if len(tickers) == 0:
                        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
                    else:
                        msg = ""
                        strangTickermsg = ""
                        for ticker in tickers:
                            name = tickerNameMap[ticker]
                            try:

                                strangTickermsg = "{ticker}:{name}".format(
                                    ticker = ticker,
                                    name = name
                                )
                                strr = tickerStatMap[ticker]
                                price = str(si.get_live_price(ticker))
                #                ex_desc = get_exchDisp(ticker)
                                msg += "{ticker} ({name}): цена ${price} \n".format(
                                    ticker = ticker,
                                    name = name,
                                    price = price
                                )
                                msg += strr
                            except Exception as e:
                                print(e)
                    
                    if msg == "":
                        msg = "Извините, по этим компаниям мы не смогли узнать цену. Попробуйте еще раз!\n" + strangTickermsg
                    
                    res['response']['text'] = msg
                    return
                    
                    


if __name__ == "__main__":
    x = threading.Thread(target=thread_function, args=())
    x.start()
    
# 1.0801479816436768
#    textForm = req['request']['original_utterance'].upper()
    textForm = "генерал электрик".upper().replace(",", "").replace(" и ", " ").replace("пожалуйста", "").replace("например о", "").replace("чтото о" , "").replace("что-то о" , "").replace("расскажи о" , "").replace("расскажи о" , "").replace("-","").replace("INC.", "").replace("GROUP", "").replace("CORPORATION", "").lstrip()
    
    listHelp = ["ПОМОЩЬ", "ЧТО ТЫ УМЕЕШЬ?", "ЧТО ТЫ УМЕЕШЬ", "ЧТО УМЕЕШЬ", "ЧТО УМЕЕШЬ?"]
    listAbout = "ВИКИ О"
    listWeek= ["ЗА НЕДЕЛЮ О","ЗА НЕДЕЛЮ"]
    listWeek2= ["ЗА ДВЕ НЕДЕЛИ О","ЗА ДВЕ НЕДЕЛИ","ЗА 2 НЕДЕЛИ О","ЗА 2 НЕДЕЛИ"]
    listWeek3= ["ЗА ТРИ НЕДЕЛИ О","ЗА ТРИ НЕДЕЛИ","ЗА 3 НЕДЕЛИ О","ЗА 3 НЕДЕЛИ"]
    listWeek4= ["ЗА МЕСЯЦ О","ЗА МЕСЯЦ"]
    
    if textForm in listHelp:
        # Помощь
        
        msg = "Я умею информировать тебя о котировках на акции фондового рынка США \n" + \
            "Например Ты можешь сказать: расскажи об AAPL или NVDA\n" + \
            "А я Тебе отвечу: AAPL (Apple Inc., NASDAQ): цена $242.2100067138672\n" + \
            "Или можешь спросить у меня иноврмацию о компании!" + \
            "Например Ты можешь сказать: Вики о AAPL"

        print(msg)
        
        
    if textForm.find(listAbout) != -1:
        text = textForm
        text = text.replace(listAbout, "").lstrip()
        tickers = getTickers(text)
        msg, url, name = getCompaniInfo(tickers)
        if url == "":
            print(msg)
        else:
            print(msg)
            print(get_suggests(name, url))
        
    
    isFound = False
    isFound2 = False
    isFound3 = False
    isFound4 = False
    for i in listWeek:
        if textForm.find(i) != -1:
            isFound = True
            break
            
    if isFound:
        
        for l in listWeek:
            textForm = textForm.replace(l, "").lstrip()
        msg = getMsg_by_interval(textForm, 7)
        print(msg)
        
    else:
#        isFound2 = False
        for i in listWeek2:
            if textForm.find(i) != -1:
                isFound2 = True
                break
        if isFound2:

           for l in listWeek2:
              textForm = textForm.replace(l, "").lstrip()
           msg = getMsg_by_interval(textForm, 14)
           print(msg)
           
        else:
            isFound3 = False
            for i in listWeek3:
                if textForm.find(i) != -1:
                    isFound3 = True
                    break
            if isFound3:

               for l in listWeek3:
                  textForm = textForm.replace(l, "").lstrip()
               msg = getMsg_by_interval(textForm, 21)
               print(msg)
               
            else:
                isFound4 = False
                for i in listWeek4:
                    if textForm.find(i) != -1:
                        isFound4 = True
                        break
                if isFound4:

                   for l in listWeek4:
                      textForm = textForm.replace(l, "").lstrip()
                   msg = getMsg_by_interval(textForm, 31)
                   print(msg)
                   
                else:
                
                    tickerStatMap, tickerNameMap, tickers = getTickers(textForm)
                    msg = ""
                    if len(tickers) == 0:
                        msg = "Извините, по таким тикерам ничего не найдено. Попробуйте еще раз!"
                    else:
                        msg = ""
                        strangTickermsg = ""
                        for ticker in tickers:
                            name = tickerNameMap[ticker]
                            try:

                                strangTickermsg = "{ticker}:{name}".format(
                                    ticker = ticker,
                                    name = name
                                )
                                strr = tickerStatMap[ticker]
                                price = str(si.get_live_price(ticker))
                #                ex_desc = get_exchDisp(ticker)
                                msg += "{ticker} ({name}): цена ${price} \n".format(
                                    ticker = ticker,
                                    name = name,
                                    price = price
                                )
                                msg += strr
                            except Exception as e:
                                print(e)
                    
                    if msg == "":
                        msg = "Извините, по этим компаниям мы не смогли узнать цену. Попробуйте еще раз!\n" + strangTickermsg

                    print(msg)
