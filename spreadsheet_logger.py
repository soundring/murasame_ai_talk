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

def save_conversation_log(user_message, ai_response):
    timestamp = datetime.now().isoformat()

    conversation_history_sheet.append_row([timestamp, user_message, ai_response, "", ""])

    create_conversation_summary(user_message, ai_response)

def get_user_info():
    return user_info_cell_value

def get_recent_conversation_history():
    rows = conversation_history_sheet.get_all_values()
     # 最後の5件を取得
    recent_rows = rows[-5:]

    conversations_json = json.dumps({
          i: {
              "timestamp": row[0],
              "user_message": row[1],
              "ai_response": row[2]
          }
          for i, row in enumerate(recent_rows, start=1)
      })

    return conversations_json

def get_conversation_summary():
    rows = conversation_summary_sheet.get_all_values()

    total_rows = len(rows)

    # 直近5件を除く
    summary = [row[0] for row in rows[1:total_rows-5]] if total_rows > 6 else []
    return "\n".join(summary)
    

def create_conversation_summary(user_message, ai_response):
    messages = [
        {
            "role": "system",
            "content": (
                "以下のユーザーの発言とAIの発言を1行で要約してください。"
                "この要約は会話の際に用いるため、ユーザーとAIの発言を区別しながら、重要なポイントを簡潔にまとめてください。\n\n"
                "ユーザーは⚪︎⚪︎、AIは⚪︎⚪︎のような簡潔なものでいい。"
            )
        },
        {"role": "user", "content": "ユーザーの発言:" + user_message + "\n\n" + "AIの発言" + ai_response},
    ]

    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages
    )

    summary = response.choices[0].message.content

    conversation_summary_sheet.append_row([summary])