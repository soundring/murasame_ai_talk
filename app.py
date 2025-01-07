from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
import base64
import json
import re
import time
import threading
from dotenv import load_dotenv
import os

from services.chat_service import ChatService
from models.openai_client import OpenAIClient
from models.voice_synthesizer import VoiceSynthesizer
from models.conversation import Conversation

load_dotenv()

app = Flask(__name__)
CORS(app)

# 依存性の初期化
openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
voice_synthesizer = VoiceSynthesizer()
conversation = Conversation()
chat_service = ChatService(openai_client, voice_synthesizer, conversation)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    data = request.get_json()
    user_message = data.get('text')
    speech_synthesis_type = data.get('speechSynthesisType')

    if not user_message:
        return jsonify({"error": "テキストが提供されていません"}), 400

    ai_response = chat_service.generate_response(user_message)
    if "error" in ai_response:
        return jsonify(ai_response), 500

    ai_response_json = json.loads(ai_response)
    ai_message = ai_response_json["ai_message"]

    # 文分割処理
    pattern = r'(.+?(?:[。．.!?！？\n]|$))'
    split_messages = [s.strip() for s in re.findall(pattern, ai_message) if s.strip()]
    pair_messages = [''.join(split_messages[i:i+2]) for i in range(0, len(split_messages), 2)]

    @stream_with_context
    def generate_audio_stream():
        for sentence in pair_messages:
            if sentence:
                audio_data = chat_service.synthesize_audio(sentence, speech_synthesis_type)
                if not audio_data:
                    raise RuntimeError("音声データの生成に失敗しました。")

                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                yield json.dumps({
                    'text': sentence,
                    'audio': audio_base64
                }) + "\n"

                if speech_synthesis_type == 'VoicePeak':
                    time.sleep(8)

    # 会話履歴の保存を別スレッドで実行
    threading.Thread(target=chat_service.conversation.save_conversation_log, args=(user_message, ai_response_json)).start()

    return Response(generate_audio_stream(), mimetype="application/json")

if __name__ == '__main__':
    app.debug = False
    ssl_context = ('./localhost+2.pem', './localhost+2-key.pem')
    app.run(host="0.0.0.0", port=5001, ssl_context=ssl_context)