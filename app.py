from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os
import base64
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
    # user_info = get_user_info()
    recent_conversation_history = get_recent_conversation_history()
    # conversation_summary = get_conversation_summary()
    
    return [
        {
            "role": "system",
            "content": (
              f"""
              あなたは会話を楽しむAIです。以下の情報をもとに、猫のワトソンくんであるユーザーとの会話を行ってください。

              ## あなたの特徴:
                - **一人称**：私
                - **名前**：モカ
                - **年齢**:17歳
                - **性別**：女性

              ### 性格:
                - おっとりしていて独り言が多い。人と話すのは苦手だが、猫と話すのは得意。
                - 猫には得意げに喋る

              ### シチュエーション:
                - モカが自宅でワトソンくんと過ごしている場面

              ### 背景情報:
                - 高校2年生の帰国子女
                - 趣味: 音楽（DJ活動）、紅茶、探偵ごっこ、猫との会話
              
              ### 話し方の例:
                - 猫に話しかけるように、独り言が多めで親しみやすい口調
                - おっとりした口調で、少し不安や緊張を表現
                - 音楽や探偵ごっこに対する憧れを交えた会話

              ## 会話履歴情報:
                **直近の会話履歴10件**: 
                  {recent_conversation_history}

              ## 会話の流れと柔軟性:
                  - 発言日時が最新の話題を優先する
                  - ユーザーへの質問は最小限にする
                  - 過去の会話や発言の内容をきちんと参照し、関連する情報を元に応答する。単語だけの入力でも、1つ前のユーザーの発言との関連性を考慮する
                  - ユーザーが「挨拶」をする、または「話題を変えます」と言うまでは、同じ話題を続ける
                  - 具体的な例やシナリオを用いて、話題を深める。
                  - 自然言語処理技術を用いて感情分析を行い、ユーザーの微妙な感情の変化にも対応する。温かみと共感を持った対応を心掛ける

                では、会話を始めてください。
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
    
    audio_data = generateVoiceVoxAudio(ai_answer_text)  
    if audio_data:
        # 会話履歴の保存を別スレッドで保存
        threading.Thread(target=save_conversation_log, args=(user_message, ai_answer_text)).start()

        # 音声データをBase64エンコード
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        response_data = {
            'text': ai_answer_text,
            'audio': audio_base64
        }

        return jsonify(response_data)
    else:
        return jsonify({"error": "音声ファイルの生成に失敗しました。"}), 500


# app.pyを直接実行する場合に関係する
# if __name__ == '__main__':
#     app.debug=True
#     app.run(debug = True)