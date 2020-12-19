# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import requests
import base64

class FacePlus:
    def __init__(self,key,secret):
        self.key = key
        self.secret = secret
        self.endpoint = 'https://api-us.faceplusplus.com'
    
    def judge_face(self,path):
        img_file = base64.encodestring(open(path, 'rb').read())
        response = requests.post(
            self.endpoint + '/facepp/v3/detect',
            {
                'Content-Type': 'multipart/from-data',
                'api_key': self.key,
                'api_secret': self.secret,
                'image_base64': img_file,
                'return_attributes': 'gender,age,headpose,facequality,eyestatus,emotion,ethnicity,beauty,mouthstatus'

            }
        )
        result = response.json()
        return result["faces"][0]["attributes"]["beauty"]["female_score"]

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


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


# @handler.add(MessageEvent, message=TextMessage)
# def message_text(event):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text=event.message.text)
#     )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    key = os.getenv('FACEPP_KEY', None)
    secret = os.getenv('FACEPP_SECRET', None)

    with open(Path(f"static/"{message_id}".jpg").absolute(),"wb") as f:

        fp = FacePlus(key,secret)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=fp.judge_face(f))
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT",5000))
    app.run(host="0.0.0.0",port=port)

# if __name__ == "__main__":
#     arg_parser = ArgumentParser(
#         usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
#     )
#     arg_parser.add_argument('-p', '--port', default=8000, help='port')
#     arg_parser.add_argument('-d', '--debug', default=False, help='debug')
#     options = arg_parser.parse_args()

#     app.run(debug=options.debug, port=options.port)
