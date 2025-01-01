import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import openai
import json

# Google Sheets API周りの設定
credentials = Credentials.from_service_account_file('credentials.json', scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
gc = gspread.authorize(credentials)

spreadsheet = gc.open("AIとの会話履歴")
user_info_cell_value = spreadsheet.get_worksheet(0).get('A2')[0][0]
conversation_history_sheet = spreadsheet.get_worksheet(2)
conversation_summary_sheet = spreadsheet.get_worksheet(3)

# 会話履歴の保存
def save_conversation_log(user_message, ai_response_json):
    timestamp = datetime.now().isoformat()
    ai_message = ai_response_json["ai_message"]
    topic = ai_response_json["topic"]
    importance = ai_response_json["importance"]
    emotion = ai_response_json["emotion"]

    conversation_history_sheet.append_row([timestamp, user_message, ai_message, topic, importance, emotion])

    create_conversation_summary(user_message, ai_message)

def create_conversation_summary(user_message, ai_message):
    messages = [
        {
            "role": "system",
            "content": (
                """
                あなたには以下の会話内容から要約を作成し、ユーザーの発言のキーポイントを抽出してください。
                1. 文脈（会話の背景と流れ）
                2. キーポイント（ユーザーの発言の重要なポイントを箇条書き）

                ## 要約しない場合
                単純な挨拶や別れの言葉など重要でない情報のみの場合は、「 {} 」とだけ出力してください。

                ## 出力形式
                {
                  "context": "（ここに会話の文脈を書く）",
                  "key_points": ["（「ユーザーは」で始めるキーポイントを箇条書き）"],
                }
                """
            )
        },
        {"role": "user",
        "content": (
            f"""
            ## 会話内容
                ユーザー: {user_message}
                AI: {ai_message}
            """
          )
        },
    ]

    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages
    )

    timestamp = datetime.now().isoformat()
    summary = response.choices[0].message.content

    if summary == '{}':
        return;

    conversation_summary_sheet.append_row([timestamp, summary])

# ユーザー情報の取得
def get_user_info():
    return user_info_cell_value

# 直近の会話履歴を取得
def get_recent_conversation_history():
    rows = conversation_history_sheet.get_all_values()
     
    recent_rows = rows[-10:] if len(rows) > 10 else rows[1:]

    sorted_rows = sorted(recent_rows, key=lambda row: row[0], reverse=True)
    
    conversations = ""

    conversations += "\n".join([
        f"""
          ## 発言日時: {row[0]}
          - 私の発言: {row[1]}
          - あなたの返答: {row[2]}
        """
        for row in sorted_rows if len(row) >= 1
    ])

    return conversations

# 要約データを取得
def get_conversation_summary():
    rows = conversation_summary_sheet.get_all_values()

    if len(rows) <= 1:
      return json.dumps({})

    total_rows = len(rows)
    if total_rows <= 11:
        # 行数が11以下の場合、ヘッダーを除いたすべての行を使用
        summary_rows = rows[1:]
    else:
        # 直近の10件を除いた要約データを使用
        summary_rows = rows[1:total_rows-10]

    sorted_rows = sorted(summary_rows, key=lambda row: row[0], reverse=True)
    summary_json = json.dumps([
        {
            "timestamp": row[0],
            "要約": row[1]
        }
        for row in sorted_rows
    ])

    return summary_json
    

