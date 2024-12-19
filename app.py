from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os
import tempfile
import threading
from text2VoiceVox import generateVoiceVoxAudio
# from text2Coeiroink import playCoeiroink

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
    user_info = get_user_info()
    recent_conversation_history = get_recent_conversation_history()
    conversation_summary = get_conversation_summary()

    print(recent_conversation_history)

    return [
        {
            "role": "system",
            "content": (
                "あなたはユーザーと軽い雑談を楽しむAIです。以下に、ユーザーの概要情報と過去の会話履歴の要約を提供します。"
                f"ユーザーの詳細情報: {user_info}\n"
                f"過去の会話履歴の要約: {conversation_summary}\n\n"
                "以下に、ユーザーとの直近の会話履歴5件分を提供します。"
                f"直近の会話履歴: {recent_conversation_history}\n"
                "この情報をもとに、リラックスした雰囲気で会話を続けてください。\n\n"
                "詳細に踏み込まず、ユーザーが心地よく感じられるよう、優しさと共感を持って対話してください。"
                "話が噛み合うように、直近の会話内容を自然に繋げることを心がけましょう。"
                "会話を始めてください。"
            )
        },
        {"role": "user", "content": user_message}
    ]

def generate_response_from_chatgpt(user_message):
    try:
        messages = prepare_messages(user_message)
        response = openai.chat.completions.create(
            model = "gpt-4o-mini",
            messages = messages
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
    
    ai_answer_text = generate_response_from_chatgpt(user_message)
    
    audio_filename = generateVoiceVoxAudio(ai_answer_text)
    if audio_filename:
        # 会話履歴の保存を別スレッドで保存
        threading.Thread(target=save_conversation_log, args=(user_message, ai_answer_text)).start()

        return jsonify({"audio_url": audio_filename, "text": ai_answer_text})
    else:
        return jsonify({"error": "音声ファイルの生成に失敗しました。"}), 500

# 音声ファイルを取得するエンドポイント
@app.route('/audio/<filename>', methods=['GET'])
def get_audio(filename):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({"error": "File not found"}), 404
    

# 音声ファイルを削除するエンドポイント
@app.route('/delete_audio/<filename>', methods=['POST'])
def delete_audio(filename):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    try:
        os.remove(file_path)
        print(f"音声ファイル {file_path} が削除されました。")
        return jsonify({"status": "File deleted"}), 200
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# app.pyを直接実行する場合に関係する
# if __name__ == '__main__':
#     app.debug=True
#     app.run(debug = True)