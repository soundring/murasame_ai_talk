from typing import List, Dict, Any
from models.conversation import Conversation
from models.openai_client import OpenAIClient
from models.voice_synthesizer import VoiceSynthesizer
from system_prompt import system_instructions_prompt, speech_analysis_prompt, character_settings_prompt

class ChatService:
    def __init__(self, openai_client: OpenAIClient, voice_synthesizer: VoiceSynthesizer, conversation: Conversation):
        self.openai_client = openai_client
        self.voice_synthesizer = voice_synthesizer
        self.conversation = conversation

    def prepare_messages(self, user_message: str) -> List[Dict[str, str]]:
        user_info = self.conversation.get_user_info()
        recent_history = self.conversation.get_recent_history()
        summary = self.conversation.get_summary(user_message)
        
        return [
            {
                "role": "system",
                "content": (
                    f"{system_instructions_prompt}\n\n"
                    f"{speech_analysis_prompt}\n\n"
                    f"{character_settings_prompt}\n\n"
                    "## 現在存在するカテゴリー:\n"
                    "この中に当てはまらない場合は、新しいカテゴリを自由に追加してください。\n"
                    f"{','.join(self.conversation.processor.categories)}\n\n"
                    "## ユーザー情報:\n"
                    f"{user_info['user_info']}\n"
                )
            },
            {
                "role": "user",
                "content": (
                    "## 過去の会話の要約:\n"
                    f"{summary}\n\n"
                    "## 会話履歴:\n"
                    f"{recent_history}\n\n"
                    "## ユーザーのメッセージ:\n"
                    f"{user_message}"
                )
            }
        ]

    def generate_response(self, user_message: str) -> Dict[str, Any]:
        messages = self.prepare_messages(user_message)
        return self.openai_client.generate_response(messages)

    def synthesize_audio(self, text: str, synthesis_type: str) -> bytes:
        return self.voice_synthesizer.synthesize(text, synthesis_type)