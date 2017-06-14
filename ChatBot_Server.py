import sys
from io import BytesIO
import random
import tornado.ioloop
import tornado.web
import transitions
import telegram
# for has install pygraphviz
#from transitions.extensions import GraphMachine as Machine
#hasusegraph = True
# for can not install pygraphviz

from transitions import Machine
hasusegraph = False

from firebase import firebase
import requests
import re

from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)

firebase = firebase.FirebaseApplication('https://infinite-city.firebaseio.com',None)

game_setting = {
    '名字':'無限地城',
    '關於':'這是一個在 telegram 上，探索未知地下城的遊戲\n玩法輕鬆簡單\n動動手指就能開始玩',
    '開頭圖片' : 'https://i.imgur.com/59v7gnG.png'
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
    
    def on_enter_wait(self,update):
        print('[control] wait next command')

    def on_enter_command(self,update):
        print('[control] handle ',update.message.text)
        #global mapmachine
        global users_gamemachine
        if update.message.text.strip() == 'start':
            if users_gamemachine.get(update.message.chat.id)==None:
                text = update.message.chat.first_name + update.message.chat.last_name + " 玩家您好，歡迎來到 [" + game_setting['名字'] + "]"
                update.message.reply_photo(photo=game_setting['開頭圖片'])
                update.message.reply_text(text=text)
                print('[control] create')
                # create user transitions
                users_gamemachine[update.message.chat.id] = gameMachine()
                users_gamemachine[update.message.chat.id].handle(update)
                users_chatid.append(update.message.chat.id)
                # get user data from firebase
                global firebase
                user_data = firebase.get('/',update.message.chat.id)
                if user_data == None:
                    #create player
                    user_data = {'username' : update.message.chat.first_name + update.message.chat.last_name,'money':0}
                    #update firebase
                    firebase.put('/',update.message.chat.id,user_data)                
                users_info[update.message.chat.id] = user_data
            else:
                text = update.message.chat.first_name + update.message.chat.last_name + " 玩家你已經在 [" + game_setting['名字'] + "]\n盡情冒險吧!"
                update.message.reply_photo(photo=game_setting['開頭圖片'])
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
        #global mapmachine
        #mapmachine.handle(update)
        if 'hello' in update.message.text or '哈囉' in update.message.text:
            self.sayhello(update)
            return

        if users_gamemachine.get(update.message.chat.id)==None:
            update.message.reply_text(text="請使用 /start 開始進行冒險")
        else:
            users_gamemachine[update.message.chat.id].handle(update)
        self.back(update)

    def on_enter_hello(self,update):
        print('[control]say hello')
        reply_markup = telegram.ReplyKeyboardHide()
        update.message.reply_text(text="你好！快樂玩遊戲吧",reply_markup=reply_markup)
        self.back(update)
        

controlmachine = controlMachine(
    states=[
        'wait','command','echo','hello'
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
            'source' : ['command','echo','hello'],
            'dest' : 'wait'
        },
        {
            'trigger' : 'sayhello',
            'source' : 'echo',
            'dest' : 'hello'
        }
    ],
    initial='wait'
)

'''
,
    show_conditions=True,
    title='遊戲命令操作'
'''

'''
,
            show_conditions=True,
            title='遊戲引擎操作'
'''

class gameMachine(Machine):
    def __init__(self):
        states=['town','roomroute','roomevent','menu','menu_command','roomevent_handle']
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
            'dest' : 'roomevent_handle',
            'conditions' : 'is_handle_roomevent'
        },
        {
            'trigger' : 'handle',
            'source' : 'roomevent_handle',
            'dest' : 'roomroute'
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
            'source' : ['town','roomroute','roomevent','roomevent_handle'],
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
        },
        {
            'trigger' : 'leavemenu',
            'source' : 'menu_command',
            'dest' : 'roomevent_handle',
            'conditions' : 'open_in_roomevent_handle'
        }
        ]
        self.machine = Machine(
            model = self,
            states = states,
            transitions = transitions,
            initial=states[0],
            before_state_change = 'save_last_state'
        )
        self.curr_map = None
        self.hasevent = True
        self.haschoose = True
        self.laststate = 'town'
        self.menukeyboard = [['玩家資訊'],['退出選單']]
        self.eventtype = 0

    def save_last_state(self,update):
        if self.state!='menu' and self.state!='menu_command':
            self.laststate = self.state

    def is_going_roomroute(self,update):
        return update.message.text == "出發去地下城"

    def is_choose_roomroute(self,update):
        if map_room_node.route.get(update.message.text)!=None:
            if self.curr_map.hasroad(map_room_node.route[update.message.text]):
                print('I choose '+update.message.text)
                self.hasevent = self.curr_map.chooseroad(map_room_node.route[update.message.text])
                self.curr_map = getattr(self.curr_map,map_room_node.route[update.message.text])
                global map_room_node_list
                map_room_node_list.append(self.curr_map)
                self.haschoose = True
                self.eventtype = random.randint(1,3)
                return self.haschoose
        #update.message.reply_text(text="抱歉，那裡沒有路")
        self.haschoose = False
        return self.haschoose
        

    def is_handle_roomevent(self,update):
        if self.eventtype == 1:
            #['不理他'],['陪他回城鎮'],['戳他']
            if update.message.text == "不理他":
                return True
            elif update.message.text == "陪他回城鎮":
                return True
            elif update.message.text == "戳他":
                return True
            else:
                return False
        elif self.eventtype == 2:
            #['用50元使出急凍光線'],['用20元使出水槍!'],['沒錢']
            if update.message.text == "用50元使出急凍光線":
                return True
            elif update.message.text == "用20元使出水槍!":
                return True
            elif update.message.text == "沒錢":
                return True
            else:
                return False
        elif self.eventtype == 3:
            #['用力開'],['輕輕開'],['不開']
            if update.message.text == "用力開":
                return True
            elif update.message.text == "輕輕開":
                return True
            elif update.message.text == "不開":
                return True
            else:
                return False
        else:
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
        reply_markup = telegram.ReplyKeyboardMarkup([['出發去地下城']])
        update.message.reply_photo(photo='https://i.imgur.com/dvtgbZH.png')
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
        update.message.reply_photo(photo = map_room_node.photo[self.curr_map.style])
        self.haschoose = True

    def on_exit_roomroute(self,update):
        #self.laststate = ''
        if not self.haschoose:
            update.message.reply_text(text="抱歉，那裡沒有路")
        
    def on_enter_roomevent(self,update):
        print('I at roomevent')
        if self.hasevent:
            # appear event
            if self.eventtype == 1:
                reply_markup = telegram.ReplyKeyboardMarkup([['不理他'],['陪他回城鎮'],['戳他']])
                update.message.reply_photo(photo='https://i.imgur.com/74EwCsa.png')
                update.message.reply_text(text="你在地城遇到了人\n你打算...",reply_markup=reply_markup)
            elif self.eventtype == 2:
                reply_markup = telegram.ReplyKeyboardMarkup([['用50元使出急凍光線'],['用20元使出水槍!'],['沒錢']])
                update.message.reply_photo(photo='https://i.imgur.com/k2lvzpX.png')
                update.message.reply_text(text="你在地城遇到了魔物\n突然發現旁邊有些秘笈，但似乎需要付出一些代價\n你打算...",reply_markup=reply_markup)
            elif self.eventtype == 3:
                reply_markup = telegram.ReplyKeyboardMarkup([['用力開'],['輕輕開'],['不開']])
                update.message.reply_photo(photo='https://i.imgur.com/n7JeMIE.png')
                update.message.reply_text(text="你在地城遇到了奇特的寶箱\n你打算...",reply_markup=reply_markup)
            else:
                reply_markup = telegram.ReplyKeyboardMarkup([['handle!'],['handle!']])
                update.message.reply_text(text="你遇到了些事情\n請選擇",reply_markup=reply_markup)
        else:
            self.noevent(update)

    def on_enter_roomevent_handle(self,update):
        reply_markup = telegram.ReplyKeyboardMarkup([['OK!']])
        update.message.reply_text(text="以下是事件的結果",reply_markup=reply_markup)
        if self.eventtype == 1:
            #['不理他'],['陪他回城鎮'],['戳他']
            if update.message.text == "不理他":
                get_money = random.randint(80,120)
                text="天阿，因為你沒有理他\n發現他是魔物偽裝的\n打敗取得 "+str(get_money)+" 元!"
                update.message.reply_text(text=text)
                users_info[update.message.chat.id]['money'] += get_money          
            elif update.message.text == "陪他回城鎮":
                update.message.reply_text(text="被他當作是變態\n為了解釋，只好給他 50 元")
                users_info[update.message.chat.id]['money'] -= 50  
            elif update.message.text == "戳他":
                update.message.reply_text(text="沒想到從衣服當中掉出 200 元\n因為不好意思拿，把錢還給他")
        elif self.eventtype == 2:
            #['用50元使出急凍光線'],['用20元使出水槍!'],['沒錢']
            if update.message.text == "用50元使出急凍光線":
                if users_info[update.message.chat.id]['money'] < 50:
                    update.message.reply_text(text = "錢不夠發動秘笈\n但魔物自己跑掉了")
                else:
                    get_money = random.randint(30,49)
                    text = "使出! 急凍光線\n效果十分顯著!\n突然發現逃跑的魔物掉了"+str(get_money)+"元"
                    update.message.reply_text(text =text)
                    users_info[update.message.chat.id]['money'] -= 50
                    users_info[update.message.chat.id]['money'] += get_money 
            elif update.message.text == "用20元使出水槍!":
                if users_info[update.message.chat.id]['money'] < 20:
                    update.message.reply_text(text = "錢不夠發動秘笈\n只好自己逃跑")
                else:
                    update.message.reply_text(text = "使出! 水槍\n效果十分 不 顯著!\n幸好魔物以為只是有蟲子咬他")
                    users_info[update.message.chat.id]['money'] -= 20
            elif update.message.text == "沒錢":
                text = "魔物看你身上只有 " + str(users_info[update.message.chat.id]['money']) + "元\n從身上拿了 10 元給你就走了"
                update.message.reply_text(text=text)
                users_info[update.message.chat.id]['money'] += 10
        elif self.eventtype == 3:
            #['用力開'],['輕輕開'],['不開']
            text = ""
            get_money = 0
            if update.message.text == "用力開":
                get_money = random.randint(200,300)
                text = "一個用力過猛，寶箱解體\n發現掉出 " + str(get_money) +" 元"
            elif update.message.text == "輕輕開":
                get_money = random.randint(50,100)
                text = "輕輕開發現打不開\n但小縫隙掉出 " + str(get_money) +" 元"
            elif update.message.text == "不開":
                get_money = random.randint(10,20)
                text = "雖然不敢開，但是發現旁邊有散落的金錢 " + str(get_money) +" 元"

            update.message.reply_text(text=text)
            users_info[update.message.chat.id]['money'] += get_money

        firebase.put('/',update.message.chat.id,users_info[update.message.chat.id])

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
            text = '玩家名稱 : '+users_info[update.message.chat.id]['username'] + '\n擁有金錢 : '+str(users_info[update.message.chat.id]['money'])
            update.message.reply_text(text = text)
            self.to_menu(update)
            return
            
        self.leavemenu(update)
        

    def open_in_town(self,update):
        return self.laststate == 'town'

    def open_in_roomroute(self,update):
        return self.laststate == 'roomroute'

    def open_in_roomevent(self,update):
        return self.laststate == 'roomevent'

    def open_in_roomevent_handle(self,update):
        return self.laststate == 'roomevent_handle'

users_gamemachine = {}
users_chatid = []
map_room_node_list = []

users_info = {}

# map tree struct

class map_room_node():
    route = {"前進":'middle',"右轉":'right',"左轉":'left',"後退":'back'}
    photo = {
        1 : 'https://i.imgur.com/cDUTV1S.png',
        2 : 'https://i.imgur.com/KD4F1yr.png',
        3 : 'https://i.imgur.com/aWDrMl9.png',
        4 : 'https://i.imgur.com/FsHFWdi.png',
        5 : 'https://i.imgur.com/l9TAgon.png',
        6 : 'https://i.imgur.com/7jW982q.png',
        7 : 'https://i.imgur.com/tzRzrvO.png'
        }
    
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
    
        keyboard_middle = keyboard_middle[::-1]
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


def get_ngrok_https_url():
    response = requests.get('http://127.0.0.1:4040')
    if response.status_code != requests.codes.ok:
        print('please open ngrok!')
        sys.exit(1)
    result = re.findall('{\\\\"URL\\\\":\\\\"https://.*.ngrok.io\\\\",\\\\"Proto\\\\":\\\\"https\\\\"',str(response.text))
    result = re.findall(':\\\\".*[.]ngrok[.]io',result[0])
    print('get : '+result[0][3:])
    return result[0][3:]


API_token = '392530414:AAEAbUyz7rybDFv14ig7NzEA53trQdNYq30'
#Webhook_URL = 'https://6d887d72.ngrok.io'
# local
#Webhook_URL = get_ngrok_https_url()
# use heroku
Webhook_URL = "https://stormy-atoll-60260.herokuapp.com/"

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
        id = self.get_argument(name='id',default='0')
        print("get id = "+id)
        id = int(id)
        if id-1 >= len(users_chatid):
            self.write('no this transition!')
            return
        try:
            self.set_header("Content-Type", "image/png")
            if hasusegraph:
                byte_io = BytesIO()
                if id == None or id == 0:
                    controlmachine.graph.draw(byte_io,prog='dot',format='png')
                else:
                    users_gamemachine[users_chatid[id-1]].graph.draw(byte_io,prog='dot',format='png')

                byte_io.seek(0)
                data = byte_io.read(1024)
                while data != b'':
                    self.write(data)
                    data = byte_io.read(1024)
                byte_io.close()                
            else:
                filename = ''
                reader = open(filename,'rb')
                data = reader.read(1024)
                while data:
                    self.write(data)
                    data = reader.read(1024)
                reader.close()
            self.finish()
            return
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
        (r"/",MainHandler)
        #(r"/show",ShowHandler),
    ])
    app.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.current().start()
