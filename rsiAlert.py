"""
This code study the price of some crypto coins and the RSI indicator to send an e-mail when a good oportunity to buy is open 
"""
import time
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import talib
import numpy
import smtplib
import csv
from numpy import genfromtxt
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
import requests, traceback
from requests.exceptions import Timeout
import socket


#variables para recorrer las monedas
key = ""
index = 0
monedas = ["SHIBUSDT","MATICUSDT", "BNBUSDT", "DOGEUSDT", "ADAUSDT", "CHZUSDT", "ETHUSDT", "XRPUSDT", "DOTUSDT"]
#print(len(monedas))
numMonedas = len(monedas)
banderas = numpy.zeros((numMonedas, 1), dtype=bool)
startTime = time.time()


#ciclo infinito
while True:
    """
    # Cliente binance
    client = Client("",
                    "")
    client.ping()
    key = client.stream_get_listen_key()
    """
    # pausa de 1.5 seg para no ecceder lim de peticiones binance
    time.sleep(10)



    try:

        # envio de stay alive cada 30 minutos
        if time.time() - startTime > 1800:
            client.stream_keepalive(key)
            startTime = time.time()
        #ping para mantener viva la conexion
        client.ping()

        #Se usa index como indice al recorrer las monedas
        if index == numMonedas:
            index = 0

        klines = client.get_historical_klines(monedas[index], Client.KLINE_INTERVAL_4HOUR, "12 days ago UTC")
        #print(klines)
        #se guardan las klines en un archivo csv
        f = open('box.csv', 'w', newline='')
        writter = csv.writer(f, delimiter=',')
        for candle in klines:
            writter.writerow(candle)
        f.close()

        #se toman los datos del csv y se toman las columnas necesarias para el rsi
        myData = genfromtxt('box.csv', delimiter=',')
        close = myData[:, 4]
        print(close)
        rsi = talib.RSI(close, 14)

        #se manda un correo si el rsi deciende de 32
        if rsi[len(rsi)-1] < 32 and rsi[len(rsi)-2] >= 32:
            if banderas[index] == False:
                print("--------------------")
                print(rsi)
                print(monedas[index])
                print(rsi[len(rsi)-1])
                print(rsi[len(rsi)-2])
                print(datetime.datetime.now())
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login('correoAqui', 'contraseñaAqui')
                #mensaje = "Alerta:"+str(monedas[index])+"\n"+str(datetime.datetime.now())
                msg = MIMEMultipart()
                msg['Subject'] = 'Alerta ' + monedas[index] + "!"
                body = str(datetime.datetime.now())
                msg.attach(MIMEText(body, 'plain'))
                mensaje = msg.as_string()
                server.sendmail('correoAqui', 'correoDestino', mensaje)
                server.quit()
                banderas[index] = True
        elif rsi[len(rsi)-1] > 32 and rsi[len(rsi)-2] <= 32:
            banderas[index] = False
        index = index + 1
    except ConnectionError:
        print("exception time out ------------------------------------------------------")
        # Cliente binance
        # del client
        #para evitar el error peer
        time.sleep(0.01)
        client = Client("","", {"timeout": 10})
        key = client.stream_get_listen_key()
    except:
        print("exception all ")
        time.sleep(3000)
        # Cliente binance
        # del client
        #para evitar el error peer
        time.sleep(0.01)
        client = Client("","", {"timeout": 10})
        key = client.stream_get_listen_key()
