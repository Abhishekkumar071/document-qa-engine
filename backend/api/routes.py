from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from backend.services.document_processor import DocumentProcessor
from backend.services.llm_service import LLMService
from backend.services.rag_engine import RAGEngine

router = APIRouter()
doc_processor = DocumentProcessor()
llm_service = LLMService()
rag_engine = RAGEngine()

class SummarizeRequest(BaseModel):
    document_text: str
    max_length: int = 500

class AskRequest(BaseModel):
    document_text: str
    question: str

@router.post("/summarize")
async def summarize_document(request: SummarizeRequest):
    try:
        summary = await llm_service.summarize(request.document_text, request.max_length)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_question(request: AskRequest):
    try:
        answer = await rag_engine.answer_question(request.document_text, request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-and-process")
async def upload_and_process(file: UploadFile = File(...)):
    try:
        text = await doc_processor.extract_text_from_pdf(file)
        return {"filename": file.filename, "message": "Processed successfully", "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))