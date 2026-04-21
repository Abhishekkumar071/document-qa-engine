import logging
from typing import List
from fastapi import UploadFile
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.core.config import Config

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def extract_text_from_pdf(self, file: UploadFile) -> str:
        try:
            content = await file.read()
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise ValueError("No text could be extracted")
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)