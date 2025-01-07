from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os
import base64
import threading
from system_prompt import system_prompt
from text2VoicePeak import generateVoicePeakAudio
from text2VoiceVox import generateVoiceVoxAudio
import json
import re
import time

from spreadsheet_logger import save_conversation_log, get_recent_conversation_history, get_conversation_summary, get_user_info

load_dotenv()

# baseurlとAPIキー設定
openai.api_key = os.getenv('API_KEY')
openai.base_url = "https://api.deepseek.com"

app = Flask(__name__)

# CORSを全てのオリジンに許可する
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


def prepare_messages(user_message):
    user_info = get_user_info()
    recent_conversation_history = get_recent_conversation_history()
    conversation_summary = get_conversation_summary(user_message)
    print(conversation_summary)
    return [
        {
          "role": "system",
          "content": (
            f"{system_prompt}\n\n"
            "## ユーザー情報:\n"
            f"{user_info}\n"
          )
        },
        {
          "role": "user",
          "content":(
            "## 過去のユーザーの発言から抽出されたキーポイント:\n"
            f"{conversation_summary}\n\n"
            "## 会話履歴(文脈理解にのみ使用すること):\n"
            f"{recent_conversation_history}\n\n"
            "## ユーザーのメッセージ:\n"
            f"{user_message}"
          )
        }
    ]

def generate_response_from_chatgpt(user_message):
    try:
        messages = prepare_messages(user_message)
        response = openai.chat.completions.create(
            model = "deepseek-chat",
            messages = messages,
            response_format={"type": "json_object"},
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# 音声認識後のテキストをChatGPTに投げるエンドポイント
@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    data = request.get_json()
    user_message = data.get('text')
    speechSynthesisType = data.get('speechSynthesisType')

    if not user_message:
        return jsonify({"error": "テキストが提供されていません"}), 400

    ai_response = generate_response_from_chatgpt(user_message)
    ai_response_json = json.loads(ai_response)
    ai_message = ai_response_json["ai_message"]

    # 句読点または行末で区切る
    pattern = r'(.+?(?:[。．.!?！？\n]|$))'

    # 文を分割し、空白や空文字列を除外
    split_messages = [s.strip() for s in re.findall(pattern, ai_message) if s.strip()]

    # 短時間の音声合成アプリの呼び出しを減らすために２センテンスごとに
    pair_messages = [''.join(split_messages[i:i+2]) for i in range(0, len(split_messages), 2)]

    @stream_with_context
    def generate_audio_stream():
        for sentence in pair_messages:
            if sentence:
                audio_data = (
                    generateVoicePeakAudio(sentence) if speechSynthesisType == 'VoicePeak' 
                    else generateVoiceVoxAudio(sentence) if speechSynthesisType == 'VoiceVox' 
                    else None
                )
                if audio_data:
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    json_response = {
                        'text': sentence,
                        'audio': audio_base64
                    }
                    yield json.dumps(json_response) + "\n"
                    
                    # voicepeakを短時間で連続して実行するとエラーが発生するため、2秒待機
                    time.sleep(6) if speechSynthesisType == 'VoicePeak' else None
                else:
                    raise RuntimeError("音声データの生成に失敗しました。")
                

    # 会話履歴の保存を別スレッドで保存
    threading.Thread(target=save_conversation_log, args=(user_message, ai_response_json)).start()

    return Response(generate_audio_stream(), mimetype="application/json")

# app.pyを直接実行する場合に関係する
if __name__ == '__main__':
    app.debug=False
    ssl_context = ('./localhost+2.pem', './localhost+2-key.pem')
    app.run(host="0.0.0.0", port=5001, ssl_context=ssl_context)