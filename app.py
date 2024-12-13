from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os
import tempfile
from text2VoiceVox import generateVoiceVoxAudio
# from text2Coeiroink import playCoeiroink

load_dotenv()

# OpenAIのAPIキー設定
openai.api_key = os.getenv('API_KEY')

app = Flask(__name__)

# CORSを全てのオリジンに許可する
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

def generate_response_from_chatgpt(user_text):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages= [
              {"role": "system", "content": "You are a helpful assistant."},
              {"role": "user", "content": user_text} 
            ]
        )
        # TODO: 会話履歴更新
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

# 音声認識後のテキストをChatGPTに投げるエンドポイント
@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    data = request.get_json()
    user_text = data.get('text')

    if not user_text:
        return jsonify({"error": "No text provided"}), 400
    
    response_text = generate_response_from_chatgpt(user_text)
    # TODO: 会話履歴更新


    audio_filename = generateVoiceVoxAudio(response_text)
    if audio_filename:
        return jsonify({"audio_url": audio_filename, "text": response_text})
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