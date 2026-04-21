import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_community.vectorstores import Chroma
from backend.core.config import Config
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            self.embeddings = None
        
        self.llm_service = LLMService()
        self.vector_store = None
    
    async def answer_question(self, document_text: str, question: str) -> str:
        chunks = self.text_splitter.split_text(document_text)
        relevant_chunks = await self._retrieve_relevant_chunks(chunks, question)
        context = "\n\n".join(relevant_chunks)
        
        prompt = f"Based on the following context, please answer the question. If the answer is not in the context, say 'I do not have enough information.'\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        return await self.llm_service.generate_text(prompt)
    
    async def _retrieve_relevant_chunks(self, chunks: List[str], question: str, top_k: int = 5) -> List[str]:
        if not self.embeddings:
            return chunks[:top_k]
        
        self.vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            persist_directory=Config.VECTOR_STORE_DIR
        )
        search_results = self.vector_store.similarity_search(question, k=top_k)
        return [doc.page_content for doc in search_results]