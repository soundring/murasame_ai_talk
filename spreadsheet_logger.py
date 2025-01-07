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
def get_conversation_summary(user_message):
  response = openai.chat.completions.create(
      model = "deepseek-chat",
      messages = [
      {
          "role": "system",
          "content": (
              """
              以下の文言から、発言内容のカテゴリ名を選択し、カテゴリ名だけを出力してください。

              ### 現在存在するカテゴリ:
              - アドバイス
              - キャリア
              - クリエイター
              - ソフトウェアエンジニア
              - ブログ
              - 飲み物
              - 運動
              - 会話
              - 確認
              - 学習
              - 感情
              - 技術
              - 休息
              - 健康
              - 購入
              - 仕事
              - 時間管理
              - 自己理解
              - 自然とアウトドア活動
              - 質問
              - 趣味
              - 食事
              - 食文化
              - 食料
              - 性格
              - 創作
              - 天気
              - 伝統
              - 読書
              - 日常生活
              - 料理
              - その他
              """
          )
      },
      { "role": "user", "content": user_message },
    ],
      response_format={"type": "text"},
  )

  target_category = response.choices[0].message.content

  if target_category == '':
    return json.dumps([])

  rows = conversation_summary_sheet.get_all_values()

  if len(rows) <= 1:
      return json.dumps([])

  target_category_rows = [row for row in rows[1:] if row[0] == target_category]

  if not target_category_rows:
      return json.dumps([])

  user_conversation_summaries = [
    {
        "role": "user",
        "content": row[2],
        "dateTime": row[5]
    }
    for row in target_category_rows
  ]

  return json.dumps(user_conversation_summaries)
