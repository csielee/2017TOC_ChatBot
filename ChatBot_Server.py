import tornado.ioloop
import tornado.web
import transitions
import telegram
import json

API_token = '392530414:AAEAbUyz7rybDFv14ig7NzEA53trQdNYq30'
Webhook_URL = 'https://48cff438.ngrok.io'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")

    def post(self):
        try:
            update = telegram.Update.de_json(json.loads(self.request.body),bot)
            update_json = json.loads(self.request.body)
            text = update.message.text
            #update.message.reply_text(text)
            custom_keyboard = [['top-left','top-right'],['bottom-left','bottom-right']]
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
            bot.send_message(chat_id=update.message.chat_id, text=text,reply_markup=reply_markup)
            bot.send_photo(chat_id=update.message.chat_id, photo='http://newsimg.5054399.com/uploads/userup/1705/1619192I627.jpg')
            print(update_json['message']['from']['first_name'].strip()+update_json['message']['from']['last_name'].strip()+' : '+text)
        except Exception as error:
            print('error by [',error,']')
        finally:
            self.write("ok")
        
if __name__ == '__main__': 
    bot = telegram.Bot(token=API_token)
    if not bot:
        sys.exit(1)
    print('Hello ,this bot is '+bot.get_me()['first_name']+' ,username : '+bot.get_me()['username'])
    if not bot.set_webhook(Webhook_URL):
        print("Webhook setup failed")
        sys.exit(1)
    else:
        print("Webhook OK!")
    app = tornado.web.Application([
        (r"/",MainHandler),
    ])
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
