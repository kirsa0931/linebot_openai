from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

file1_path = '狼人殺data.txt'
file2_path = '對局data.txt'
file3_path = '對局微調.txt'
recorded_messages_file = 'recorded_messages.txt'

# 用读取模式打开文件
with open(file1_path, 'r', encoding='utf-8') as file1:
    background_knowledge = file1.read()

with open(file2_path, 'r', encoding='utf-8') as file2:
   Game_iformation = file2.read()
    
with open(file3_path, 'r', encoding='utf-8') as file3:
   fine_tuning_data = file3.read()

def GPT_response(text):
    # 接收回應
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": background_knowledge},
        {"role": "user", "content": fine_tuning_data},
        {"role": "user", "content": Game_iformation},
        {"role": "user", "content": text}
    ]
)

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == "輪到6號發言":
        with open(recorded_messages_file, 'r', encoding='utf-8') as f:
             recorded_messages = f.read()
        try:
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": recorded_messages}
                {"role": "user", "content": "請以號碼6號進行發言，點評別的玩家的發言並且最後說出你要投的對象並說明原因，限定在80個字以內"}
            ]
        )
            GPT_answer = response['choices'][0]['message']['content']
            print(GPT_answer)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=GPT_answer))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
      elif msg == "遊戲結束":
         with open(recorded_messages_file, 'w', encoding='utf-8') as f:
             f.truncate(0)
      else:
         # 否则，将用户的发言写入记录文件
         with open(recorded_messages_file, 'a', encoding='utf-8') as f:
             f.write(msg + '\n')
        

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
