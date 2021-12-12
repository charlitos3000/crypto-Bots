from binance.client import Client
import talib as ta
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pymongo
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase

#Cliente binance con permisos para crear ordenes
client = Client("oodVBFYA5fAlEk41fe42eesZWNBAecxJT1DC9Xl6YZPefxes5PhPMTvysla9T99X",
                "X6QSTiYSp4e9MMj799Hh3zeCp8KrAXqkVwYl3AThX743GgggPvkheBgFZIToVSdm")
#Cliente DB
dbClient = pymongo.MongoClient("mongodb+srv://carlos:solrac@cluster0.hyoyh.mongodb.net/Project0?retryWrites=true&w=majority")

#documentos de la base de datos
orden = dbClient['orden']
shibbusd = orden['SHIBBUSD']
abierta = shibbusd['abierta']
cerrada = shibbusd['cerrada']

startTime = time.time()

#_id maximo de los documentos de la base
topA = 0
topC = 0

#cantidad de busd a usar (1 seria todo)
cantidad = .5

#identificador de conexion con binance
key = client.stream_get_listen_key()

while(True):

    try:
        #Señales para mantener activa la conexion con binance
        client.ping()
        client.stream_keepalive(key)
    except Exception as e:
        print(e)
        #Cliente binance con permisos para crear ordenes
        client = Client("oodVBFYA5fAlEk41fe42eesZWNBAecxJT1DC9Xl6YZPefxes5PhPMTvysla9T99X",
                "X6QSTiYSp4e9MMj799Hh3zeCp8KrAXqkVwYl3AThX743GgggPvkheBgFZIToVSdm")
        #identificador de conexion con binance
        key = client.stream_get_listen_key()
    
    #Se toman los ultimos valores _id de la db
    db = abierta.find()
    for r in db:
        topA = r['_id']
    db = cerrada.find()
    for r in db:
        topC = r['_id']

    #se calcula el macd apartir de datos de velas de binance
    klines = client.get_historical_klines('SHIBBUSD', Client.KLINE_INTERVAL_1HOUR, "6 days ago UTC")
    open_time = [int(entry[0]) for entry in klines]
    close = [float(entry[4]) for entry in klines]
    close_array = np.asarray(close)
    new_time = [datetime.fromtimestamp(time/1000) for time in open_time]
    macd, macdsignal, macdhist = ta.MACD(close_array, fastperiod=12, slowperiod=26, signalperiod=9)
    #mitad = (int(macd[len(macd)-2])+int(macd[len(macd)-1]))/2

    #orden cerrada(se busca abrir una nueva operación)
    if(topA == topC):        
        """
        print(macdsignal[len(macdsignal)-2])
        print("<") 
        print(macd[len(macd)-2])
        print(macdsignal[len(macdsignal)-1])
        print(">") 
        print(macd[len(macd)-1])
        print("------")
        """
        #Si macdseñal cruza a macd se compra
        #if(float(macdsignal[len(macdsignal)-2]) < float(macd[len(macd)-2]) and float(macd[len(macd)-1]) < float(macdsignal[len(macdsignal)-1])):
        if(float(macdsignal[len(macdsignal)-2]) > float(macd[len(macd)-2]) and float(macd[len(macd)-1]) > float(macdsignal[len(macdsignal)-1])):
            print("entro") 
            
            order = client.get_asset_balance(asset='BUSD')
            cantBusd = float(order['free'])*cantidad
            order = client.get_margin_price_index(symbol='SHIBBUSD')
            cantMoneda = int(cantBusd/float(order['price']))
            print("cantidad "+ str(cantMoneda))
            
            order = client.order_market_buy(
            symbol='SHIBBUSD',
            quantity=cantMoneda)

            #se actualiza la base de datos con la nueva orden
            pivote = float(order['fills'][0]['price']) * .99
            data = {"_id":str(int(topA) + 1),"orderId":str(order['orderId']),"tiempo":str(order['transactTime']),
            "busd":str(order['cummulativeQuoteQty']),"entrada":str(order['fills'][0]['price']),"pivote":pivote}
            abierta.insert_one(data)

            #Se notifica de la compra por correo
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('botcarlos3000@gmail.com', 'Solracfree1')
            msg = MIMEMultipart()
            msg['Subject'] = 'Se compro shib'
            body = str(datetime.now())+"\nSe compraron "+str(cantBusd)+" dollares a un precio de "+str(order['fills'][0]['price'])
            msg.attach(MIMEText(body, 'plain'))
            mensaje = msg.as_string()
            server.sendmail('botcarlos3000@gmail.com', 'carloscriptomonedas1@gmail.com', mensaje)
            server.quit()
            print("se compro")


    #orden abierta(se busca cerrar la operación o actualizar el pivote)
    #elif(float(macdsignal[len(macdsignal)-2]) > float(macd[len(macd)-2]) and float(macd[len(macd)-1]) > float(macdsignal[len(macdsignal)-1])):
    else:
        #se toma la información de la ultima orden abierta
        db = abierta.find()
        for r in db:
            topA = r['_id']
            pivote = r['pivote']
            busd = r['busd']
        order = client.get_margin_price_index(symbol='SHIBBUSD')

        #Si el precio de la moneda
        if(float(order['price']) <= float(pivote)):
            #Se vende el total de la moneda
            order = client.get_asset_balance(asset='SHIB')
            order2 = client.order_market_sell(
            symbol='SHIBBUSD',
            quantity=int(float(order['free'])))

            ganancia = float(order2['cummulativeQuoteQty']) - float(busd)
            
            #Se actualiza la base de datos
            data = {"_id":str(topA),"orderId":str(order2['orderId']),"tiempo":str(order2['transactTime']),
            "busd":str(order2['cummulativeQuoteQty']),"ganancia":ganancia}
            cerrada.insert_one(data)

            #Se notifica de la venta por correo
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('botcarlos3000@gmail.com', 'Solracfree1')
            msg = MIMEMultipart()
            msg['Subject'] = 'Se vendio shib'
            body = str(datetime.now())+"\nSe vendieron  shib por "+str(order2['cummulativeQuoteQty'])+" dollares"
            msg.attach(MIMEText(body, 'plain'))
            mensaje = msg.as_string()
            server.sendmail('botcarlos3000@gmail.com', 'carloscriptomonedas1@gmail.com', mensaje)
            server.quit()
            print("se vendio")

        #Si el precio de la moneda sube se actualiza el pivote del ultimo documento
        elif(float(order['price']) >= float(pivote)*1.02):
            """
            abierta.update_one({
              '_id':topA 
            },{
              '$set': {
                'pivote': order['price']
              }
            }, upsert=False)
            print("se actualizo")
            """
            #se toma la información de la ultima orden abierta
            db = abierta.find()
            for r in db:
                topA = r['_id']
                pivote = r['pivote']
                busd = r['busd']
            order = client.get_margin_price_index(symbol='SHIBBUSD')
            #Si el precio de la moneda
            if(float(order['price']) <= float(pivote)):
                #Se vende el total de la moneda
                order = client.get_asset_balance(asset='SHIB')
                order2 = client.order_market_sell(
                symbol='SHIBBUSD',
                quantity=int(float(order['free'])))
                ganancia = float(order2['cummulativeQuoteQty']) - float(busd)
                #Se actualiza la base de datos
                data = {"_id":str(topA),"orderId":str(order2['orderId']),"tiempo":str(order2['transactTime']),
                "busd":str(order2['cummulativeQuoteQty']),"ganancia":ganancia}
                cerrada.insert_one(data)
                #Se notifica de la venta por correo
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login('botcarlos3000@gmail.com', 'Solracfree1')
                msg = MIMEMultipart()
                msg['Subject'] = 'Se vendio shib'
                body = str(datetime.now())+"\nSe vendieron  shib por "+str(order2['cummulativeQuoteQty'])+" dollares"
                msg.attach(MIMEText(body, 'plain'))
                mensaje = msg.as_string()
                server.sendmail('botcarlos3000@gmail.com', 'carloscriptomonedas1@gmail.com', mensaje)
                server.quit()
                print("se vendio")

    #se pausa 10 segundos para no pasar el limite de consultas/operaciones permitidas de binance
    print(".",end='',flush=True)
    time.sleep(10)

    """
    if(time.time() - startTime >= 180):
        quit()
    """