import sys
from io import BytesIO
import random
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
        mapmachine.handle(update)
        
        

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
        self.curr_map = None
        self.hasevent = True

    def is_going_roomroute(self,update):
        return update.message.text == "go!"

    def is_choose_roomroute(self,update):
        '''
        if action == "前進":
            action = 'middle'
            return self.curr_map.hasroad(action)
        if action == "左轉":
            action = 'left'
            return self.curr_map.hasroad(action)
        if action == "右轉":
            action = 'right'
            return self.curr_map.hasroad(action)
        if action == "後退":
            action = 'back'
            return self.curr_map.hasroad(action)
        '''
        if map_room_node.route.get(update.message.text)!=None:
            return self.curr_map.hasroad(map_room_node.route[update.message.text])
        update.message.reply_text(text="抱歉，那裡沒有路")
        return False
        

    def is_handle_roomevent(self,update):
        return update.message.text == "handle!"

    def is_back_town(self,update):
        return update.message.text == "back!"

    def on_enter_town(self,update):
        print('I at town')
        reply_markup = telegram.ReplyKeyboardMarkup([['go!']])
        update.message.reply_text(text="你正在城鎮\n想出發去地下城嗎?",reply_markup=reply_markup)

    def on_enter_roomroute(self,update):
        print('I at roomroute')
        # first enter
        if self.curr_map == None:
            self.curr_map = map_room_node(7)
        # show keyboard and text
        reply_markup = telegram.ReplyKeyboardMarkup(self.curr_map.keyboard)
        update.message.reply_text(reply_markup=reply_markup,text=self.curr_map.__str__())

    def on_exit_roomroute(self,update):
        print('I choose '+update.message.text)
        self.hasevent = self.curr_map.chooseroad(map_room_node.route[update.message.text])
        self.curr_map = getattr(self.curr_map,map_room_node.route[update.message.text])
        
    def on_enter_roomevent(self,update):
        print('I at roomevent')
        if self.hasevent:
            # appear event
            reply_markup = telegram.ReplyKeyboardMarkup([['handle!'],['handle!']])
            update.message.reply_text(text="你遇到了些事情\n請選擇",reply_markup=reply_markup)
        else:
            self.noevent(update)
        

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
            'trigger' : 'noevent',
            'source' : 'roomevent',
            'dest' : 'roomroute',
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

# map tree struct

class map_room_node():
    route = {"前進":'middle',"右轉":'right',"左轉":'left',"後退":'back'}
    
    def __init__(self,roomstyle = -1,prev_room_node = None):
        if roomstyle == -1:
            roomstyle = random.randint(1,7)
        self.style = roomstyle
        self.keyboard = []
        keyboard_middle = []
        if roomstyle % 2 == 1:
            self.right = None
            keyboard_middle.append("右轉")
        roomstyle //= 2
        if roomstyle % 2 == 1:
            self.middle = None
            self.keyboard.append(["前進"])
        roomstyle //= 2
        if roomstyle % 2 == 1:
            self.left = None
            keyboard_middle.append("左轉")
        self.keyboard.append(keyboard_middle)
        if prev_room_node != None:
            self.back = prev_room_node
            self.keyboard.append(["後退"])

    def hasroad(self,road):
        return hasattr(self,road)

    def chooseroad(self,road):
        if not hasattr(self,road):
            return False
        if getattr(self,road) == None:
            if road == 'middle':
                self.middle = map_room_node(prev_room_node=self)
            if road == 'left':
                self.left = map_room_node(prev_room_node=self)
            if road == 'right':
                self.right = map_room_node(prev_room_node=self)
            if road == 'back':
                self.back = map_room_node(prev_room_node=self)
            return True
        else:
            return False
            
            

    def __str__(self):
        return "來到了"+str(self.style)+"號道路\n謹慎選擇吧!"

    


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
