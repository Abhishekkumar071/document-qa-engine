import requests

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def summarize(self, document_text: str, max_length: int = 500) -> str:
        response = self.session.post(f"{self.base_url}/api/summarize", json={"document_text": document_text, "max_length": max_length})
        response.raise_for_status()
        return response.json().get("summary", "")
    
    def ask_question(self, document_text: str, question: str) -> str:
        response = self.session.post(f"{self.base_url}/api/ask", json={"document_text": document_text, "question": question})
        response.raise_for_status()
        return response.json().get("answer", "")