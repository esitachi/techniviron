# Realtime AI Backend (WebSockets + Supabase)

## Overview

This project is a **real-time AI backend** that simulates a live conversational session using **WebSockets**.
It demonstrates production-grade backend patterns including:

- Bi-directional real-time communication
- LLM token streaming
- Session and event persistence using Supabase (PostgreSQL)
- Post-session automation to generate conversation summaries

The focus of this assignment is **backend architecture and system design**, not UI/UX.

---

## Key Features

- **Realtime WebSocket Sessions**
  - Persistent WebSocket connection per session
  - Low-latency, bidirectional message flow

- **LLM Streaming**
  - AI responses are streamed token-by-token
  - Asynchronous, non-blocking design
  - Graceful handling of API failures or quota limits

- **Conversation State Management**
  - Maintains conversation context across turns
  - Logs all user and AI messages chronologically

- **Supabase Persistence**
  - Session metadata stored in PostgreSQL
  - Detailed event log for every interaction

- **Post-Session Automation**
  - On WebSocket disconnect, conversation history is analyzed
  - LLM generates a concise session summary
  - Summary and session end time are persisted

- **Simple Frontend**
  - Minimal HTML page with connect/send/disconnect buttons
  - Used only to demonstrate WebSocket behavior

---

## Tech Stack

- **Backend Framework:** FastAPI (Python, async)
- **Realtime Transport:** WebSockets
- **LLM API:** OpenAI-compatible API (provider-agnostic)
- **Database:** Supabase (PostgreSQL)
- **Environment Management:** python-dotenv
- **Frontend:** Plain HTML + JavaScript

---

## Architecture Flow

1. Client connects via WebSocket `/ws/session/{session_id}`
2. Backend creates or updates a session record
3. User messages are streamed to the LLM
4. AI responses are streamed back token-by-token
5. All messages are logged as session events
6. On WebSocket disconnect:
   - Conversation history is fetched from the database
   - LLM generates a concise session summary
   - Session end time and summary are saved

---

## Database Schema

### Sessions Table

```sql
create table sessions (
  session_id text primary key,
  start_time timestamptz,
  end_time timestamptz,
  summary text
);
```

### Session Events Table

```sql
create table session_events (
  id bigserial primary key,
  session_id text references sessions(session_id),
  event_type text,
  content text,
  created_at timestamptz default now()
);
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- Supabase project
- OpenAI-compatible API key (OpenAI, OpenRouter, Groq, etc.)

---

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd techniviron
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1   # optional

SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

> **Note:** The service role key is required for server-side inserts and updates.

---

### 4. Run the Server

```bash
uvicorn app.tech_main:app --reload --port 8001
```

---

## How to Test

### Option 1: Browser Console

```javascript
let ws = new WebSocket(
  "ws://127.0.0.1:8001/ws/session/test_" + Date.now()
);

ws.onopen = () => {
  ws.send("Hello, explain WebSockets simply");
};

ws.onmessage = (e) => console.log("AI:", e.data);

// Close connection to trigger summary
ws.close();
```

---

### Option 2: Simple HTML Frontend

1. Open `index.html` in a browser
2. Click **Connect**
3. Send a message
4. Click **Disconnect**
5. Check Supabase tables for session summary

---

## Error Handling & LLM Quota

This backend is designed to be **resilient**:

- If LLM streaming fails (e.g., API quota exceeded):
  - The WebSocket does **not crash**
  - A fallback AI message is stored
  - Post-session summary still executes

This mirrors production-grade AI system behavior.

---

## Design Decisions

- **WebSockets over REST:** Required for real-time, low-latency communication
- **Event-based persistence:** Enables auditing and post-session analysis
- **Session upsert:** Prevents duplicate primary key errors
- **Provider-agnostic LLM design:** Easy to switch providers
- **Async-first architecture:** Non-blocking I/O for scalability

---

## Project Structure

```
techniviron/
├── app/
│   └── tech_main.py
├── index.html
├── requirements.txt
├── README.md
└── .env   # not committed
```

---

## Conclusion

This project demonstrates how to build a **real-time AI backend** using modern backend patterns such as streaming AI responses, persistent conversation memory, and automated post-session analysis. It closely mirrors how production AI agents and conversational SaaS systems are implemented.

---

## Author

**Eshaan Hegde**
