I will add later.

<img width="1919" height="1079" alt="first" src="https://github.com/user-attachments/assets/304f619f-8b05-4b49-b214-9787608735dd" />
<img width="1911" height="958" alt="second" src="https://github.com/user-attachments/assets/c254dd3a-3439-479d-8f4f-7a346eed00b4" />
<img width="1516" height="426" alt="third" src="https://github.com/user-attachments/assets/e282e164-2651-408b-bc8e-14ed1e292a29" />
```
Client (React or Streamlit)
        │  document_id, question
        ▼
FastAPI (auth middleware, rate limiting)
        │
        ├─ POST /documents          → extract text, chunk, embed ONCE, store, return document_id
        ├─ POST /documents/{id}/ask → look up doc's vector store by id, retrieve, generate
        ├─ POST /documents/{id}/summarize
        └─ DELETE /documents/{id}   → auth-scoped to the owner, not global wipe

Postgres (documents, users, chat_history)   ← swap SQLite when you add real users
Chroma / pgvector (persisted per document_id, embedded once)



document-qa-engine/
├── backend/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── api/
│   │   └── routes.py
│   └── services/
│       ├── document_processor.py
│       ├── llm_service.py
│       └── rag_engine.py
├── frontend/
│   ├── app.py
│   └── api_client.py
├── requirements.txt
└── .gitignore

```
Prioritized roadmap
Data model: add documents table + document_id; stop passing raw document_text over the wire.
Fix the embedding re-computation — embed once per upload, persist, query by ID.
Lock down /clear-all and add minimal auth (API key to start, JWT if you want to go further).
Tighten CORS, sanitize error responses, add upload size/type limits.
Add a /health endpoint, a Dockerfile, and 10-ish tests. This is the fastest way to make the repo look production-minded even before every feature is perfect.
Swap SQLite → Postgres and wire in real user accounts once auth exists — this is what actually unlocks multi-tenancy.
Optional but strong for interviews: add streaming responses (SSE/websocket) from Groq instead of waiting for the full completion — shows you understand UX at scale, and it's a natural extension of code you already have.
