import sys
from io import BytesIO
import tornado.ioloop
import tornado.web
import transitions
import telegram
#from transitions.extensions import GraphMachine
from transitions import Machine

class controlMachine(Machine):
    def __init__(self,**machine_configs):
        self.machine = Machine(
            model = self,
            **machine_configs
        )
        self.help_str = "底下是我能接受的指令\n/start\n/photo\n/keyboard\n/help"

    def is_take_command(self,update):
        if (update.message.text[0] == '/'):
            update.message.text = update.message.text[1:len(update.message.text)]
            return True
        else:
            return False
    

    def on_enter_wait(self,update):
        print('[control] wait next command')

    def on_enter_command(self,update):
        print('[control] handle ',update.message.text)
        if update.message.text.strip() == 'start':
            update.message.reply_text(text="指揮官您好，有什麼可以為你服務嗎?")
            self.back(update)
            return
        if update.message.text == 'photo':
            update.message.reply_photo(photo='http://newsimg.5054399.com/uploads/userup/1705/1619192I627.jpg')
            self.back(update)
            return
        if update.message.text == 'keyboard':
            keyboard = [['/start'],['/photo'],['/keyboard'],['/help']]
            reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
            update.message.reply_text(reply_markup=reply_markup,text="這是選單")
            self.back(update)
            return
        if update.message.text == 'help':
            update.message.reply_text(text=self.help_str)
            self.back(update)
            return
        #default
        text = "抱歉，我看不懂這個命令\n" + self.help_str
        update.message.reply_text(text=text)
        self.back(update)

    def on_enter_echo(self,update):
        print('[control] echo message and handle map')
        update.message.reply_text(text=update.message.text)
        self.back(update)
        global mapmachine
        mapmachine.handle(update.message.text)
        
        

controlmachine = controlMachine(
    states=[
        'wait','command','echo'
    ],
    transitions=[
        {
            'trigger' : 'getcommand',
            'source' : 'wait',
            'dest' : 'command',
            'conditions' : 'is_take_command'
        },
        {
            'trigger' : 'getcommand',
            'source' : 'wait',
            'dest' : 'echo',
            'unless' : 'is_take_command'
        },
        {
            'trigger' : 'back',
            'source' : ['command','echo'],
            'dest' : 'wait'
        }
    ],
    initial='wait',
)

class mapMachine(Machine):
    def __init__(self,**machine_configs):
        self.machine = Machine(
            model = self,
            **machine_configs
        )

    def is_going_roomroute(self,action):
        return action == "go!"

    def is_choose_roomroute(self,action):
        return action == "choose!"

    def is_handle_roomevent(self,action):
        return action == "handle!"

    def is_back_town(self,action):
        return action == "back!"

    def on_enter_town(self,action):
        print('I at town')

    def on_enter_roomroute(self,action):
        print('I at roomroute')

    def on_enter_roomevent(self,action):
        print('I at roomevent')

mapmachine = mapMachine(
    states=[
        'town','roomroute','roomevent'
    ],
    transitions=[
        {
            'trigger' : 'handle',
            'source' : 'town',
            'dest' : 'roomroute',
            'conditions' : 'is_going_roomroute'
        },
        {
            'trigger' : 'handle',
            'source' : 'town',
            'dest' : 'town',
            'unless' : ['is_going_roomroute','is_back_town']
        },
        {
            'trigger' : 'handle',
            'source' : 'roomroute',
            'dest' : 'roomevent',
            'conditions' : 'is_choose_roomroute'
        },
        {
            'trigger' : 'handle',
            'source' : 'roomroute',
            'dest' : 'roomroute',
            'unless' : ['is_choose_roomroute','is_back_town']
        },
        {
            'trigger' : 'handle',
            'source' : 'roomevent',
            'dest' : 'roomroute',
            'conditions' : 'is_handle_roomevent'
        },
        {
            'trigger' : 'handle',
            'source' : 'roomevent',
            'dest' : 'roomevent',
            'unless' : ['is_handle_roomevent','is_back_town']
        },
        {
            'trigger' : 'handle',
            'source' : ['roomevent','roomroute'],
            'dest' : 'town',
            'conditions' : 'is_back_town'
        }
    ],
    initial='town',
)


API_token = '392530414:AAEAbUyz7rybDFv14ig7NzEA53trQdNYq30'
Webhook_URL = 'https://911ffcb4.ngrok.io'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!")

    def post(self):
        try:
            update_json = tornado.escape.json_decode(self.request.body)
            update = telegram.Update.de_json(tornado.escape.json_decode(self.request.body),bot)
            text = update.message.text
            print(update_json['message']['from']['first_name'].strip()+update_json['message']['from']['last_name'].strip()+' : '+update_json['message']['text'])
            
            controlmachine.getcommand(update)
            #update_json = json.loads(self.request.body)
            #update_json = tornado.escape.json_decode(self.request.body)
            
            #update.message.reply_text(text)
            #custom_keyboard = [['top-left','top-right'],['bottom-left','bottom-right']]
            #reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
            #bot.send_message(chat_id=update.message.chat_id, text=text,reply_markup=reply_markup)
            #bot.send_photo(chat_id=update.message.chat_id, photo='http://newsimg.5054399.com/uploads/userup/1705/1619192I627.jpg')
            
            
        except Exception as error:
            print('error by [',error,']')
        finally:
            self.write("ok")

class ShowHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            self.set_header("Content-Type", "image/png")
            self.write('');
        except Exception as error:
            print('error by [',error,']')

        
if __name__ == '__main__': 
    global bot
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
        (r"/show",ShowHandler),
    ])
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
