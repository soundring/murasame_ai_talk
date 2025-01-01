from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os
import base64
import threading
# from text2VoiceVox import generateVoiceVoxAudio
from system_prompt import system_prompt
from text2VoicePeak import generateVoicePeakAudio
import json

from spreadsheet_logger import save_conversation_log, get_recent_conversation_history, get_conversation_summary, get_user_info

load_dotenv()

# OpenAIのAPIキー設定
openai.api_key = os.getenv('API_KEY')

app = Flask(__name__)

# CORSを全てのオリジンに許可する
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


def prepare_messages(user_message):
    # user_info = get_user_info()
    recent_conversation_history = get_recent_conversation_history()
    # conversation_summary = get_conversation_summary()
    
    return [
        {
            "role": "system",
            "content": (
              f"""
              {system_prompt}
              
              ## 直近の会話履歴10件:
                {recent_conversation_history}
              """
            )
        },
        {"role": "user", "content": user_message}
    ]

def generate_response_from_chatgpt(user_message):
    try:
        messages = prepare_messages(user_message)
        response = openai.chat.completions.create(
            # model = "gpt-4o-2024-11-20",
            model = "gpt-4o-mini",
            messages = messages,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# 音声認識後のテキストをChatGPTに投げるエンドポイント
@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    data = request.get_json()
    user_message = data.get('text')

    if not user_message:
        return jsonify({"error": "No text provided"}), 400
    
    ai_response = generate_response_from_chatgpt(user_message)
    ai_response_json = json.loads(ai_response)
    ai_message = ai_response_json["ai_message"]
    audio_data = generateVoicePeakAudio(ai_message)  
    if audio_data:
        # 会話履歴の保存を別スレッドで保存
        threading.Thread(target=save_conversation_log, args=(user_message, ai_response_json)).start()

        # 音声データをBase64エンコード
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        response_data = {
            'text': ai_message,
            'audio': audio_base64
        }

        return jsonify(response_data)
    else:
        return jsonify({"error": "音声ファイルの生成に失敗しました。"}), 500

# app.pyを直接実行する場合に関係する
if __name__ == '__main__':
    app.debug=False
    ssl_context = ('./localhost+2.pem', './localhost+2-key.pem')
    app.run(host="0.0.0.0", port=5001, ssl_context=ssl_context)