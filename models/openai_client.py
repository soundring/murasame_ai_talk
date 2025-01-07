from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IAIClient(ABC):
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        pass

class OpenAIClient(IAIClient):
    def __init__(self, api_key: str, base_url: str):
        import openai
        openai.api_key = api_key
        openai.base_url = base_url
        self.client = openai

    def generate_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={"type": "json_object"},
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return {"error": str(e)}