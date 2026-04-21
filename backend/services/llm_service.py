import logging
import aiohttp
from backend.core.config import Config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"
        self.api_endpoint = "https://api.groq.com/openai/v1/chat/completions"
    
    async def summarize(self, text: str, max_length: int = 500) -> str:
        try:
            if len(text) == 0:
                raise ValueError("Text cannot be empty")
            
            text = text[:6000] # Safe token limit
            prompt = f"Please provide a concise summary of the following document in no more than {max_length} characters.\n\nDocument:\n{text}\n\nSummary:"
            return await self._call_groq_api(prompt)
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            raise
    
    async def _call_groq_api(self, prompt: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a highly intelligent and helpful enterprise AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.7
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, json=payload, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Groq API error: {response.status} - {error_text}")
                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq API call failed: {str(e)}")
            raise
    
    async def generate_text(self, prompt: str) -> str:
        return await self._call_groq_api(prompt)