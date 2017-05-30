import sys
from io import BytesIO
import random
import tornado.ioloop
import tornado.web
import transitions
import telegram
#from transitions.extensions import GraphMachine
from transitions import Machine

game_setting = {
    '名字':'無限地城',
    '關於':'這是一個在 telegram 上，探索未知地下城的遊戲\n玩法輕鬆簡單\n動動手指就能開始玩'
    }

class controlMachine(Machine):
    def __init__(self,**machine_configs):
        self.machine = Machine(
            model = self,
            **machine_configs
        )
        self.help_str = "歡迎來到 " + game_setting['名字'] +"\n各種指令\n/start 開始遊戲\n/about 關於遊戲\n/menu 遊戲選單\n/help 幫助"
        #self.start_game = False

    def is_take_command(self,update):
        if (update.message.text[0] == '/'):
            update.message.text = update.message.text[1:len(update.message.text)]
            return True
        else:
            return False

    def is_take_startmenu_command(self,update):
        if update.message.text == "開始冒險":
            global mapmachine
            mapmachine.handle(update)
            return True
        if update.message.text == "關於遊戲":
            update.message.reply_text(text=game_setting['關於'])
            return False
        update.message.reply_text(text="抱歉，這不是合理的操作")
        return False
    

    def on_enter_wait(self,update):
        print('[control] wait next command')

    def on_enter_command(self,update):
        print('[control] handle ',update.message.text)
        #global mapmachine
        global users_gamemachine
        if update.message.text.strip() == 'start':
            if users_gamemachine.get(update.message.chat.id)==None:
                text = update.message.chat.first_name + update.message.chat.last_name + " 玩家您好，歡迎來到 [" + game_setting['名字'] + "]"
                #keyboard = [['開始冒險'],['關於遊戲']]
                #reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                update.message.reply_text(text=text)
                #self.go_startmenu(update)
                print('[control] create')
                # create user transitions
                users_gamemachine[update.message.chat.id] = gameMachine()
                users_gamemachine[update.message.chat.id].handle(update)
            else:
                text = update.message.chat.first_name + update.message.chat.last_name + " 玩家你已經在 [" + game_setting['名字'] + "]\n盡情冒險吧!"
                update.message.reply_text(text=text)
            self.back(update)
            return
        if update.message.text.strip() == 'about':
            update.message.reply_text(text=game_setting['關於'])
            self.back(update)
            return
        if update.message.text.strip() == 'photo':
            update.message.reply_photo(photo='http://newsimg.5054399.com/uploads/userup/1705/1619192I627.jpg')
            self.back(update)
            return
        if update.message.text.strip() == 'menu':
            # TODO
            if users_gamemachine.get(update.message.chat.id)==None:
                update.message.reply_text(text="抱歉，無法開啟選單\n因為你還沒開始遊戲 /start")
            else:
                if users_gamemachine[update.message.chat.id].state!='menu':
                    users_gamemachine[update.message.chat.id].openmenu(update)
                else:
                    update.message.reply_text(text="你已經開啟選單")
                    users_gamemachine[update.message.chat.id].to_menu(update)
            self.back(update)
            return
        if update.message.text.strip() == 'help':
            update.message.reply_text(text=self.help_str)
            self.back(update)
            return
        #default
        text = "抱歉，無法辨識這個命令\n" + self.help_str
        update.message.reply_text(text=text)
        self.back(update)

    def on_enter_echo(self,update):
        print('[control] echo message and handle map')
        update.message.reply_text(text=update.message.text)
        self.back(update)
        #global mapmachine
        #mapmachine.handle(update)
        if users_gamemachine.get(update.message.chat.id)==None:
            update.message.reply_text(text="請使用 /start 開始進行冒險")
        else:
            users_gamemachine[update.message.chat.id].handle(update)

        

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

class gameMachine(Machine):
    def __init__(self):
        states=['town','roomroute','roomevent','menu','menu_command']
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
            'unless' : 'is_going_roomroute'
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
        },
        {
            'trigger' : 'openmenu',
            'source' : ['town','roomroute','roomevent'],
            'dest' : 'menu'
        },
        {
            'trigger' : 'handle',
            'source' : 'menu',
            'dest' : 'menu_command',
            'conditions' : 'is_handle_menu_command'
        },
        {
            'trigger' : 'handle',
            'source' : 'menu',
            'dest' : 'menu',
            'unless' : 'is_handle_menu_command'
        },
        {
            'trigger' : 'leavemenu',
            'source' : 'menu_command',
            'dest' : 'town',
            'conditions' : 'open_in_town'
        },
        {
            'trigger' : 'leavemenu',
            'source' : 'menu_command',
            'dest' : 'roomroute',
            'conditions' : 'open_in_roomroute'
        },
        {
            'trigger' : 'leavemenu',
            'source' : 'menu_command',
            'dest' : 'roomevent',
            'conditions' : 'open_in_roomevent'
        }
        ]
        self.machine = Machine(
            model = self,
            states = states,
            transitions = transitions,
            initial=states[0],
            before_state_change = 'save_last_state',
        )
        self.curr_map = None
        self.hasevent = True
        self.haschoose = True
        self.laststate = 'town'
        self.menukeyboard = [['玩家資訊'],['退出選單']]

    def save_last_state(self,update):
        if self.state!='menu':
            self.laststate = self.state

    def is_going_roomroute(self,update):
        return update.message.text == "go!"

    def is_choose_roomroute(self,update):
        if map_room_node.route.get(update.message.text)!=None:
            if self.curr_map.hasroad(map_room_node.route[update.message.text]):
                print('I choose '+update.message.text)
                self.hasevent = self.curr_map.chooseroad(map_room_node.route[update.message.text])
                self.curr_map = getattr(self.curr_map,map_room_node.route[update.message.text])
                global map_room_node_list
                map_room_node_list.append(self.curr_map)
                self.haschoose = True
                return self.haschoose
        #update.message.reply_text(text="抱歉，那裡沒有路")
        self.haschoose = False
        return self.haschoose
        

    def is_handle_roomevent(self,update):
        return update.message.text == "handle!"

    def is_back_town(self,update):
        print('judge back!')      
        if update.message.text == "back!":
            self.haschoose = True
            return self.haschoose
        return False     

    def on_enter_town(self,update):
        print('I at town')
        self.menukeyboard = [['玩家資訊'],['退出選單']]
        self.curr_map = None
        reply_markup = telegram.ReplyKeyboardMarkup([['go!']])
        update.message.reply_text(text="你正在城鎮\n想做些什麼呢?",reply_markup=reply_markup)

    def on_enter_roomroute(self,update):
        print('I at roomroute')
        self.menukeyboard = [['玩家資訊'],['離開地下城'],['退出選單']]
        # first enter
        if self.curr_map == None:
            global map_room_node_list
            self.curr_map = map_room_node_list[random.randint(0,len(map_room_node_list)-1)]
        # show keyboard and text
        reply_markup = telegram.ReplyKeyboardMarkup(self.curr_map.keyboard)
        update.message.reply_text(reply_markup=reply_markup,text=self.curr_map.__str__())
        self.haschoose = True

    def on_exit_roomroute(self,update):
        #self.laststate = ''
        if not self.haschoose:
            update.message.reply_text(text="抱歉，那裡沒有路")
        
    def on_enter_roomevent(self,update):
        print('I at roomevent')
        if self.hasevent:
            # appear event
            reply_markup = telegram.ReplyKeyboardMarkup([['handle!'],['handle!']])
            update.message.reply_text(text="你遇到了些事情\n請選擇",reply_markup=reply_markup)
        else:
            self.noevent(update)

    def on_enter_menu(self,update):
        print('[menu]open menu')
        reply_markup = telegram.ReplyKeyboardMarkup(self.menukeyboard)
        update.message.reply_text(reply_markup=reply_markup,text="選單開啟")

    def is_handle_menu_command(self,update):
        print('[menu]detect '+update.message.text)
        for elem in self.menukeyboard:
            if update.message.text in elem:
                return True
        return False

    def on_enter_menu_command(self,update):
        print('[menu]handle '+update.message.text)
        if update.message.text == '離開地下城':
            self.to_town(update)
            return   
        if update.message.text == '玩家資訊':
            update.message.reply_text(text = "還在實作中")
            
        self.leavemenu(update)
        

    def open_in_town(self,update):
        return self.laststate == 'town'

    def open_in_roomroute(self,update):
        return self.laststate == 'roomroute'

    def open_in_roomevent(self,update):
        return self.laststate == 'roomevent'

users_gamemachine = {}
map_room_node_list = []

#mapmachine = gameMachine()

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


map_room_node_list.append(map_room_node(7))


API_token = '392530414:AAEAbUyz7rybDFv14ig7NzEA53trQdNYq30'
Webhook_URL = 'https://513f9bed.ngrok.io'

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
