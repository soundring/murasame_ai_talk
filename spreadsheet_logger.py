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
    # TODO: 要約作成の方に移動する
    ai_message = ai_response_json["ai_message"]
    category = ai_response_json["category"]
    sub_category = ai_response_json["sub_category"]
    importance = ai_response_json["importance"]
    emotion = ai_response_json["emotion"]

    conversation_history_sheet.append_row([timestamp, user_message, ai_message, category, importance, emotion])

    create_conversation_summary(user_message, category, sub_category, importance, emotion, timestamp)

def create_conversation_summary(user_message, category, sub_category, importance, emotion, timestamp):
    messages = [
        {
            "role": "system",
            "content": (
                """
                以下の会話内容から、ユーザーの発言のキーポイントを抽出してください。
                キーポイントは複数あってもいいです。

                ## キーポイントを抽出しない場合
                単純な挨拶や別れの言葉などの場合は、空文字を出力してください。
                パーソナルデータの構築に重要でない情報の場合も、空文字を出力してください。

                ## 出力形式
                「ユーザーは」で始まる文字列
                """
            )
        },
        { "role": "user", "content": user_message },
    ]

    response = openai.chat.completions.create(
        model = "deepseek-chat",
        messages = messages,
        response_format={"type": "text"},
    )

    key_point = response.choices[0].message.content

    if key_point == '':
        return;

    conversation_summary_sheet.append_row([category, sub_category, key_point, importance, emotion, timestamp])

# ユーザー情報の取得
def get_user_info():
  return user_info_cell_value

# 直近の会話履歴を取得
def get_recent_conversation_history():
    rows = conversation_history_sheet.get_all_values()
     
    recent_rows = rows[-5:] if len(rows) > 5 else rows[1:]
    sorted_rows = sorted(recent_rows, key=lambda row: row[0], reverse=True)
    
    conversations = []

    for row in sorted_rows:
        conversations.append({"role": "user", "content": row[1], "timestamp": row[0]})
        conversations.append({"role": "assistant", "content": row[2], "timestamp": row[0]})

    return json.dumps(conversations)

# 要約データを取得
# TODO: 発言にマッチするカテゴリの要約データを取得するように変更
def get_conversation_summary():
  rows = conversation_summary_sheet.get_all_values()

  if len(rows) <= 1:
      return json.dumps([])
      
  # 昨日以前の行をフィルタリング
  yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
  summary_rows = [row for row in rows[1:] if datetime.fromisoformat(row[0]) < yesterday]

  user_conversation_summaries = []
  for row in summary_rows:
    key_point = row[2]

    datetime_str = row[5]
    date_only = datetime_str.split("T")[0]
      
    user_conversation_summaries.append({"role": "user", "content": key_point, "date": date_only})

  return json.dumps(user_conversation_summaries)
