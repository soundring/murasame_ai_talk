from typing import Dict, Any
from .conversation_data_processor import ConversationDataProcessor
from .google_sheets import GoogleSheetsClient
from .openai_client import OpenAIClient
import os

class Conversation:
    def __init__(self):
        # 依存性の初期化
        sheets_client = GoogleSheetsClient(
            credentials_file="credentials.json",
            spreadsheet_name="AIとの会話履歴"
        )
        
        ai_client = OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        
        self.processor = ConversationDataProcessor(sheets_client, ai_client)

    def get_user_info(self) -> Dict[str, Any]:
        return {"user_info": self.processor.get_user_info()}

    def get_recent_history(self) -> str:
        return self.processor.get_recent_conversation_history()

    def get_summary(self, user_message: str) -> str:
        return self.processor.get_conversation_summary(user_message)
        
    def save_conversation_log(self, user_message: str, ai_response: Dict[str, Any]) -> None:
        self.processor.save_conversation_log(user_message, ai_response)