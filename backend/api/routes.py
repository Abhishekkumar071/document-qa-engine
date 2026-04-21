from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import shutil
import os

from backend.core.database import get_db, ChatMessage
from backend.core.config import Config
from backend.services.document_processor import DocumentProcessor
from backend.services.llm_service import LLMService
from backend.services.rag_engine import RAGEngine

router = APIRouter()
doc_processor = DocumentProcessor()
llm_service = LLMService()
rag_engine = RAGEngine()

# --- THESE WERE MISSING! ---
class SummarizeRequest(BaseModel):
    document_text: str
    max_length: int = 500

class AskRequest(BaseModel):
    document_text: str
    question: str
# ---------------------------

@router.post("/summarize")
async def summarize_document(request: SummarizeRequest):
    try:
        summary = await llm_service.summarize(request.document_text, request.max_length)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    try:
        # Save User Question
        user_msg = ChatMessage(session_id="default", role="user", content=request.question)
        db.add(user_msg)
        
        # Get AI Answer
        answer = await rag_engine.answer_question(request.document_text, request.question)
        
        # Save AI Answer
        ai_msg = ChatMessage(session_id="default", role="assistant", content=answer)
        db.add(ai_msg)
        db.commit()
        
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

@router.get("/history")
def get_chat_history(db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == "default").order_by(ChatMessage.timestamp.asc()).all()
    return [{"role": msg.role, "content": msg.content} for msg in messages]

@router.delete("/clear-all")
def clear_all_memory(db: Session = Depends(get_db)):
    global rag_engine
    try:
        # 1. Clear SQL DB (Chat History)
        db.query(ChatMessage).filter(ChatMessage.session_id == "default").delete()
        db.commit()
        
        # 2. Tell the current RAG engine to drop its connection to the database
        if hasattr(rag_engine, 'vector_store') and rag_engine.vector_store:
            rag_engine.vector_store = None
        
        # 3. Safely clear Vector DB folder (Bypassing Windows File Locks)
        if os.path.exists(Config.VECTOR_STORE_DIR):
            try:
                # ignore_errors=True stops Windows from crashing the app if a file is locked
                shutil.rmtree(Config.VECTOR_STORE_DIR, ignore_errors=True)
            except Exception as e:
                print(f"Warning: Could not completely delete vector folder: {e}")
        
        # Ensure the directory exists for the next upload
        os.makedirs(Config.VECTOR_STORE_DIR, exist_ok=True)
            
        # 4. Reset RAG Engine
        rag_engine = RAGEngine()
        
        return {"message": "Memory cleared successfully"}
        
    except Exception as e:
        print(f"--- DEEP CLEAN ERROR: {str(e)} ---")
        raise HTTPException(status_code=500, detail=str(e))