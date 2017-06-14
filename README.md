計算理論 - 聊天機器人 (無限地城)
===
coding by `李東霖`

[hackmd](https://hackmd.io/s/rkp0EM5e-)

![](https://i.imgur.com/59v7gnG.png)

## 使用工具與函式庫

- telegram bot
    - [Create a Telegram EchoBot](http://lee-w.github.io/posts/bot/2017/03/create-a-telegram-echobot/)
    - [開發 Telegram Bot 簡介](http://blog.30sparks.com/develop-telegram-bot-introduction/)
    - [官方 Restful API](https://core.telegram.org/bots/api)
    - [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot#table-of-contents)
- python transitions(FSM)
    - [transitions github](https://github.com/tyarkoni/transitions)
- python web framework
    - [tornado中文文本](https://tornado-zh.readthedocs.io/zh/latest/)
- HTTPS server
    - [ngrok](https://ngrok.com/)
- Google Firebase
    - [python-firebase](https://pypi.python.org/pypi/python-firebase/1.2)

## 如何執行

盡量使用 python3 來跑

### 先將必要的模組安裝起來

`$ pip install -r requirement.txt`

### 開啟 ngrok

- windows
    - 可點擊 `Start_Server.bat`
- linux
    - 可點擊 `Start_Server.sh`

### 開啟 server

這邊會自動去抓 ngrok 的 https 網址
不用去修改程式碼
但如果要使用不同的 bot ，要更新 API token

`$ python ChatBot_Server.py`

如出現 `Webhook OK!` 代表成功開啟並設定
可以開始跟 bot 對話

## 如何跟我的 bot 互動

這是一個小遊戲

需要自己打的指令如下

- /start
    - 開始遊戲
- /about
    - 關於遊戲
- /menu
    - 遊戲選單
- /help
    - 幫助

之後都會有 keyboard 協助選擇
也可以選擇亂回話，並不會導致 bot 當掉
bot 也會在回錯話時進行提醒

## 關於這個 bot

## 內容發想

一開始有思考過

- 文字魔法遊戲
- 海龜湯
- 電子小說
- 地下城

最後選擇做一個在 **地下城** 冒險的遊戲

## 實作功能

- 城鎮
- 地下城
    - 可自由冒險，有7種房間
    - 隨機生成地下城
    - 在 server 開啟期間，所有走過地城會被記錄

## 運用 telegram bot

- reply_markup
    - 方便使用者當遊戲來玩，減少打字的煩躁
- photo
    - 增加趣味性，避免單純文字的煩悶

## 運用 transitions

利用 DFA 的特性，用多個 transitions machine 做為 遊戲指令操作 跟 遊戲引擎運作

- 遊戲命令操作
    - 共有 3 個 state
    - wait 是等待使用者輸入
    - command 是已判斷為遊戲指令，並進行操作
    - echo 是將上述以外的輸入回傳並丟入遊戲引擎
    - 為所有使用者共用

- 遊戲引擎操作
    - 每個使用者有各自的 transitions machine
    - 共有 6 個 state
    - town 是使用者在城鎮時
    - roomroute 是使用者在地城中某個路口
    - roomevent 是使用者在地城中遇到事件
    - roomevent_handle 是使用者在處理遇到的事件
    - menu 是使用者開啟遊戲選單
    - menu_command 是使用者正在執行選單的功能

## 多人遊玩

因為在 server 上的 transition machine 必須要有多個才能去記錄每個使用者操作的狀態
因此使用 字典dict 結構去儲存使用者的 transition machine 與 玩家資訊

## 考慮遊戲記錄

因為目前的設計上，只要關掉 server 重開
記錄都會消失，因此就找尋了簡單的後端即時資料庫 -- firebase
來把使用者的記錄保存下來，並隨時更新
firebase 也能從後端進行修改跟觀看，方便維護
