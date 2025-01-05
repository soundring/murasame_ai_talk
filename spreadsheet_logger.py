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
                以下の会話内容から、ユーザーの発言のキーポイントを抽出してください。

                ## 要約しない場合
                単純な挨拶や別れの言葉など重要でない情報のみの場合は、「 {} 」とだけ出力してください。

                ## 出力形式
                {
                  "key_points": ["（「ユーザーは」で始めるキーポイントを箇条書き）"],
                }
                """
            )
        },
        { "role": "user", "content": user_message },
        { "role": "assistant", "content": ai_message }
    ]

    response = openai.chat.completions.create(
        model = "deepseek-chat",
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
     
    recent_rows = rows[-5:] if len(rows) > 5 else rows[1:]
    sorted_rows = sorted(recent_rows, key=lambda row: row[0], reverse=True)
    
    conversations = []

    for row in sorted_rows:
        conversations.append({"role": "user", "content": row[1], "timestamp": row[0]})
        conversations.append({"role": "assistant", "content": row[2], "timestamp": row[0]})

    return json.dumps(conversations)

# 要約データを取得
def get_conversation_summary():
  rows = conversation_summary_sheet.get_all_values()

  if len(rows) <= 1:
      return json.dumps([])
      
  # 昨日以前の行をフィルタリング
  yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
  summary_rows = [row for row in rows[1:] if datetime.fromisoformat(row[0]) < yesterday]

  # 全てのkey_pointsを繋げる
  user_conversation_summaries = []
  for row in summary_rows:
    datetime_str = row[0]
    date_only = datetime_str.split("T")[0]
    summary_json = json.loads(row[1])
    key_points = summary_json.get("key_points", [])
      
    for key_point in key_points:
      user_conversation_summaries.append({"role": "user", "content": key_point, "date": date_only})

  return json.dumps(user_conversation_summaries)
