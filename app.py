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

background_knowledge = """
    請依以下的資訊，嘗試扮演一個騎士玩家身分為“玩家6”

    以下是狼人殺遊戲的名詞解釋
    ==
    查殺:意思是預言家查驗到的狼人牌，例如:5號玩家起跳預言家，並且說8號為查殺，意思就是5號玩家查驗8號玩家為狼人
    金水:意思是預言家查驗到的好人牌
    反水:當預言家查驗到的金水玩家不相信發金水給他的預言家為真的預言家，稱該情況為反水
    起跳:指玩家在遊戲中表明自己身分的行為
    站邊:指有2個以上玩家起跳預言家的情況，剩餘玩家要在其中找到自己認為是真的的預言家，例如:1號，2號玩家起跳預言家，8號玩家認為1號玩家為真預言家，則可以說8號玩家站邊1號。站邊可以從2個情況下判斷，一個是發言時的言論，另一個則是投票環節時看玩家們的投票來判斷站邊
    倒鉤:指站邊真預言家的狼人
    後置位查殺:指預言家往還沒發言過的位置發查殺
    後置位金水:指預言家往還沒發言過的位置發金水
    反向金水:指假預言家發的查殺牌
    前置位查殺:指預言家往已經發言過的位置發查殺
    前置位金水:指預言家往已經發言過的位置發金水
    摸頭金:指狼人發真好人金水，意圖讓對方站邊自己
    金水流:指預言家投單號牌，金水牌投雙號牌，比如1號預言家，2號金水，則1號選3 5 7 9投一張，2號選1 4 6投一張
    騎金：被騎士選擇進行決鬥而使騎士以死謝罪的好人陣營玩家。
    撞：指騎士決鬥技能。
    
    
    以下是關於騎士的一些規則，依據編號由1開始往後
    
    ==
    
    1.騎士每局遊戲有一次機會可以在白天發言階段的任何玩家發言時段公佈身份牌，並選擇一名玩家與其決鬥。
    2.若決鬥玩家是狼人陣營玩家，則該狼人陣營玩家被殺死，隨即進入黑夜階段；反之則騎士死亡，白天階段流程繼續進行。
    3.決鬥死亡的狼人陣營技能不能發動。
    4.騎士的技能通常用在幫助好人陣營辨別誰是真正的預言家。
"""


def GPT_response(text):
    # 接收回應
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": background_knowledge},
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
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": msg}
            ]
        )
        GPT_answer = response['choices'][0]['message']['content']
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=GPT_answer))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
        

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
