import json
import time
import tweepy
import telebot

#llaves y tokens
apiKey = "3UoFmZMkoPM2niLdqSNOx8bHZ"
apiSecretKey = "FGSlv56Glq94bIGFkYDjGNdlizuTN59zjGTunTwehF33OUpUyG"
bearerToken = "AAAAAAAAAAAAAAAAAAAAAFidQAEAAAAAWj3ioQTt42GVEalaVNeMKkx8bAQ%3DBv0dnwtbtFnWpTqTBZLu0s0TtYL7pSrw6j62uPKTIhD5ut5IwX"
accessToken = "1387861281542221828-Gid1mKq5U27LirrxkznBsZQgaqMxSx"
accessSecretToken = "lZtQQUKO6A1bNF1jp2v2GPWT3mKnN8dpiPMFsRdFWDqTE"
listaAmigos = "1387861281542221828"
TOKEN = '1766147741:AAFBhUjT00uTFcjeiP6osJ2CglBWyO5d0uo'
#listaAmigos = ["1387861281542221828"]


#autenticaión
auth = tweepy.OAuthHandler(apiKey,apiSecretKey)
auth.set_access_token(accessToken,accessSecretToken)
api = tweepy.API(auth)

#crear el objeto para telegram
tb = telebot.TeleBot(TOKEN)

#obtener el numero de seguidores
data = api.me()
print (data._json["friends_count"])
friendsCount = data._json["friends_count"]

for tweet in tweepy.Cursor(api.friends,"1387861281542221828",tweet_mode="compat").items(friendsCount):
    listaAmigos=listaAmigos+","+str(tweet._json["id"])

#clase para tweets en tiempo real
class TweetsListener(tweepy.StreamListener):
    def on_connect(self):
        print("conectado!")
    def on_exception(self, exception):
        print(exception)
        return
    def on_limit(self, track):
        print("limite alcanzado!")
    def on_status(self,status):
        print(status.text)
        tb.send_message("1497317387", status.text)
        if "listed" in status.text or "list" in status.text or "newlistings" in status.text or "a" in status.text:
            msg = status.text
            if "R" != msg[0] and "T" != msg[1]:
                if "@" != msg[0]:
                    print(status.text)

        time.sleep(12)
    def on_error(self,status_code):
        print("Error",status_code)
        return false

##monitorear tweets en tiempo real
stream = TweetsListener()
streamingApi = tweepy.Stream(api.auth,stream)
streamingApi.filter(
    follow=[listaAmigos]
    #track=["newlistings","list","listed"]
)