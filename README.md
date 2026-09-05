I will add later.

<img width="1919" height="1079" alt="first" src="https://github.com/user-attachments/assets/304f619f-8b05-4b49-b214-9787608735dd" />
<img width="1911" height="958" alt="second" src="https://github.com/user-attachments/assets/c254dd3a-3439-479d-8f4f-7a346eed00b4" />
<img width="1516" height="426" alt="third" src="https://github.com/user-attachments/assets/e282e164-2651-408b-bc8e-14ed1e292a29" />


# Code Review: document-qa-engine

**Verdict:** Solid workshop project, working end-to-end RAG pipeline. Not production-grade yet — but the gap is a known, learnable set of patterns, not a rewrite. Rating: **4/10 as "production"**, **7/10 as "learning project that proves you can wire up a real stack."**


## The three architectural issues that matter most

These are the ones an interviewer at a product company will notice first, because they're not styling nitpicks — they're evidence of whether you understand how a real multi-user system has to be shaped.

### 1. No concept of "a document" or "a user"
`routes.py` hardcodes `session_id="default"` everywhere. Every visitor to the app shares one chat history and one document context. Two people using it at once would corrupt each other's sessions. There's no `Document` table, no `document_id`, nothing that says "this text belongs to this upload."

**Fix:** Add a `documents` table (id, filename, extracted_text or a pointer to it, created_at, owner/session_id). Every route that currently takes `document_text` in the request body should instead take a `document_id` and look the text up server-side.

### 2. Embeddings are rebuilt from scratch on every question
In `rag_engine.py`, `_retrieve_relevant_chunks` calls `Chroma.from_texts(...)` — which re-embeds the *entire document* — every time `answer_question` runs. Ask 10 questions about one PDF, you pay the embedding cost 10 times.

**Fix:** Embed once at upload time, persist the vector store keyed by `document_id`, and just query it on each question. This is also where "production" thinking shows: you're separating write-path (ingest, expensive, happens once) from read-path (query, cheap, happens often).

### 3. The frontend doesn't use your own backend upload route
`app.py` extracts PDF text locally with its own `PyPDF2` loop, instead of calling `POST /upload-and-process`. That means `document_processor.py`'s PDF logic is dead code in practice, and the full document text gets shipped from browser → API on *every* summarize/ask call instead of once at upload.

**Fix:** These three problems are really one fix. Give documents identity: upload once → store & embed once → reference by ID everywhere after. Once you do that, #1 and #2 mostly resolve themselves.

---

## Security issues

| Issue | Where | Risk |
|---|---|---|
| No auth on any endpoint | `routes.py` | Anyone can call any route |
| `DELETE /api/clear-all` has zero protection | `routes.py` | Anyone can wipe your DB + vector store |
| `CORSMiddleware(allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])` | `main.py` | Any website can call your API from a user's browser |
| Raw exception text returned to client | every route, `except Exception as e: ... detail=str(e)` | Leaks stack traces / internal paths |
| No file size / content-type validation on upload | `routes.py`, `document_processor.py` | DoS via huge files, no real MIME check beyond extension |
| No rate limiting | anywhere | One user can exhaust your Groq quota for everyone |

**Fix priority:** auth (even a simple API key or JWT) and locking down `clear-all` first — that's the one that lets a stranger destroy your data. CORS and error handling are quick wins after that.

---

## Engineering / code quality issues

- **Global mutable state**: `rag_engine` is reassigned *inside* a route handler (`clear-all` in `routes.py`). Under multiple Uvicorn workers each process has its own memory, so this silently breaks under real concurrency — a subtle bug that's exactly the kind of thing a senior engineer probes for in review.
- **Duplicate, inconsistent chunking logic**: `DocumentProcessor` and `RAGEngine` each instantiate their own `RecursiveCharacterTextSplitter`. `DocumentProcessor.chunk_text()` is never actually called in the real flow — dead code.
- **`Config.validate()` isn't enforced at startup** unless you run via `python main.py`'s `__main__` block. Running `uvicorn backend.main:app` directly (which your own comment in `requirements.txt` recommends) skips the check, so a missing API key fails silently until the first request.
- **No migrations.** `Base.metadata.create_all()` works for a single dev DB but has no story for evolving schema safely later (use Alembic).
- **No tests** — unit or integration. Even 10-15 tests around `DocumentProcessor` and `LLMService` (mocked) would meaningfully change how this reads to a reviewer.
- **No Dockerfile / containerization**, no CI (GitHub Actions), no health-check endpoint (`GET /health`) — all cheap to add, all expected by default at product companies.
- **Debug-flavored comments left in code**: `# Hardcoded to bypass cache completely`, `# Safely create the database path`, `# Bypassing Windows File Locks`. These read as scars from local debugging — clean up before someone reviews the repo.
- **Dead dependency**: `pdfplumber` is in `requirements.txt` but never imported.
- **Streamlit is fine for a demo, but say so.** For a "product-grade" pitch, either swap in a minimal React/Next frontend, or explicitly frame Streamlit as an intentional choice for an internal tool / MVP — don't let it look like you didn't know the difference.

---

## What's actually good here (don't lose this in the rewrite)

- Clean separation into `routes / services / core` — the instinct is right, just needs the document-identity fix layered on top.
- Using SQLAlchemy ORM (no raw SQL, no injection surface) — good default.
- Chroma + HuggingFace embeddings + Groq for generation is a reasonable, cheap, real RAG stack — not a toy.
- You correctly `.gitignore`'d `.env`, `*.db`, and `chroma_data/` — a lot of workshop projects get this wrong.
- The `/clear-all` "deep clean" logic handles Windows file-lock quirks (`ignore_errors=True`) — shows you actually hit and debugged a real-world problem instead of just writing happy-path code.

---

## Suggested target architecture

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
```

## Prioritized roadmap

1. **Data model**: add `documents` table + `document_id`; stop passing raw `document_text` over the wire.
2. **Fix the embedding re-computation** — embed once per upload, persist, query by ID.
3. **Lock down `/clear-all`** and add minimal auth (API key to start, JWT if you want to go further).
4. **Tighten CORS**, sanitize error responses, add upload size/type limits.
5. **Add a `/health` endpoint, a Dockerfile, and 10-ish tests.** This is the fastest way to make the repo *look* production-minded even before every feature is perfect.
6. **Swap SQLite → Postgres** and wire in real user accounts once auth exists — this is what actually unlocks multi-tenancy.
7. Optional but strong for interviews: add **streaming responses** (SSE/websocket) from Groq instead of waiting for the full completion — shows you understand UX at scale, and it's a natural extension of code you already have.

## How to talk about this in interviews

Frame it exactly as what it is: *"I built a working RAG pipeline in a workshop, then went back and re-architected the document/session model, added auth, fixed a redundant-embedding bug, and containerized it."* That before/after story is more valuable to a product company than a project that looks polished but where you can't articulate the trade-offs — because it proves you can *identify* production gaps yourself, which is the actual skill they're hiring for.
