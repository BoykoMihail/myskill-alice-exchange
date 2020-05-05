import os
import threading
import urllib.request
from queue import Queue
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


class DownloadThread(Thread):
"""
Пример скачивание файла используя многопоточность
"""

def __init__(self, name):
    """Инициализация потока"""
    Thread.__init__(self)
    self.name = name

def run(self):
    """Запуск потока"""
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
    
    msg = "%s закончил загрузку!" % (self.name)
    print(msg)
