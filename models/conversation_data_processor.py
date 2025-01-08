from typing import List, Dict, Any
import json
from datetime import datetime
from .google_sheets import GoogleSheetsClient
from .openai_client import IAIClient
from system_prompt import conversation_summary_prompt

class ConversationDataProcessor:
    def __init__(self, sheets_client: GoogleSheetsClient, ai_client: IAIClient):
        self.sheets_client = sheets_client
        self.ai_client = ai_client
        
        # ワークシートのインデックスを定義
        self.USER_INFO_WORKSHEET = 0
        self.CATEGORY_LIST_WORKSHEET = 1
        self.CONVERSATION_HISTORY_WORKSHEET = 2
        self.CONVERSATION_SUMMARY_WORKSHEET = 3
        
        # カテゴリ一覧を初期化
        self._initialize_categories()
        
    def save_conversation_log(self, user_message: str, ai_response: Dict[str, Any]):
        timestamp = datetime.now().isoformat()
        row_data = [
            timestamp,
            user_message,
            ai_response["ai_message"],
            ai_response["category"],
            ai_response["importance"],
            ai_response["emotion"]
        ]
        
        self.sheets_client.append_row(self.CONVERSATION_HISTORY_WORKSHEET, row_data)
        self._create_conversation_summary(user_message, ai_response, timestamp)
        
    def _create_conversation_summary(self, user_message: str, ai_response: Dict[str, Any], timestamp: str):
        messages = [
            {"role": "system", "content": conversation_summary_prompt},
            {"role": "user", "content": user_message},
        ]
        
        response = self.ai_client.generate_response(messages)
        conversation_summary_json = json.loads(response)

        if not conversation_summary_json.get("user_key_point"):
            return
            
        summary_data = [
            ai_response["category"],
            ai_response["sub_category"],
            conversation_summary_json["user_key_point"],
            conversation_summary_json["ai_key_point"],
            ai_response["importance"],
            ai_response["emotion"],
            timestamp
        ]
        
        self.sheets_client.append_row(self.CONVERSATION_SUMMARY_WORKSHEET, summary_data)
        
    def get_user_info(self) -> str:
        return self.sheets_client.get_cell_value(self.USER_INFO_WORKSHEET, "A2")
        
    def get_recent_conversation_history(self) -> str:
        rows = self.sheets_client.get_all_values(self.CONVERSATION_HISTORY_WORKSHEET)
        recent_rows = rows[-5:] if len(rows) > 5 else rows[1:]
        sorted_rows = sorted(recent_rows, key=lambda row: row[0], reverse=True)
        
        conversations = []
        for row in sorted_rows:
            conversations.append({
                "role": "user",
                "timestamp": row[0],
                "content": row[1],
                "category": row[3],
                "importance": row[4],
                "emotion": row[5]
            })
            conversations.append({
                "role": "assistant",
                "timestamp": row[0],
                "content": row[2]
            })
            
        return json.dumps(conversations)
        
    def _initialize_categories(self):
        """スプレッドシートからカテゴリ一覧を取得して初期化"""
        try:
            rows = self.sheets_client.get_all_values(self.CATEGORY_LIST_WORKSHEET)
            if rows:
                self.categories = [row[0] for row in rows[1:]]  # ヘッダー行をスキップ
            else:
                self.categories = []
        except Exception as e:
            print(f"カテゴリ一覧の初期化に失敗しました: {e}")
            self.categories = []

    def get_conversation_summary(self, user_message: str) -> str:
        messages = [
            {"role": "system", "content": f"適切なカテゴリを選択してください\n{','.join(self.categories)}"},
            {"role": "user", "content": user_message},
        ]
        
        target_category = self.ai_client.generate_response(messages)
        
        if not target_category:
            return json.dumps([])
            
        rows = self.sheets_client.get_all_values(self.CONVERSATION_SUMMARY_WORKSHEET)
        
        if len(rows) <= 1:
            return json.dumps([])
            
        target_category_rows = [row for row in rows[1:] if row[0] == target_category]
        
        if not target_category_rows:
            return json.dumps([])
            
        summaries = [
            {
                "role": "user",
                "category": row[0],
                "sub_category": row[1],
                "user_key_point": row[2],
                "ai_key_point": row[3] if row[3] else "",
                "importance": row[4],
                "emotion": row[5],
                "timestamp": row[6]
            }
            for row in target_category_rows
        ]
        
        return json.dumps(summaries)