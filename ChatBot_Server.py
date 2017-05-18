import tornado.ioloop
import tornado.web
import transitions
import telegram
import json

API_token = '392530414:AAEAbUyz7rybDFv14ig7NzEA53trQdNYq30'
Webhook_URL = 'https://e711fe79.ngrok.io'

bot = telegram.Bot(token=API_token)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")

    def post(self):
        update = telegram.Update.de_json(json.loads(self.request.body),bot)
        update_json = json.loads(self.request.body)
        text = update.message.text
        print(update_json['message']['from']['first_name'].strip()+update_json['message']['from']['last_name'].strip()+' : '+text)
        update.message.reply_text(text)

        self.write("ok")
        
if __name__ == '__main__': 
    print("hello 哈囉")
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