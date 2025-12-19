import os
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Clients
# -------------------------------------------------
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")  # optional, safe if not set
)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

app = FastAPI()

# -------------------------------------------------
# LLM Streaming Helper
# -------------------------------------------------
async def stream_llm_response(messages):
    async with client.responses.stream(
        model="gpt-4.1-mini",
        input=messages
    ) as stream:
        async for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta


# -------------------------------------------------
# WebSocket Endpoint
# -------------------------------------------------
@app.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # STEP 4 — Create or update session safely (UPSERT)
    supabase.table("sessions").upsert({
        "session_id": session_id,
        "start_time": datetime.utcnow().isoformat()
    }).execute()

    conversation = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]

    print(f"Session started: {session_id}")

    try:
        while True:
            # -----------------------------------------
            # Receive user message
            # -----------------------------------------
            user_message = await websocket.receive_text()

            # STEP 5A — Save user message
            supabase.table("session_events").insert({
                "session_id": session_id,
                "event_type": "user_message",
                "content": user_message
            }).execute()

            conversation.append({"role": "user", "content": user_message})

            full_ai_response = ""

            # -----------------------------------------
            # STREAM AI RESPONSE (ERROR SAFE)
            # -----------------------------------------
            try:
                async for token in stream_llm_response(conversation):
                    full_ai_response += token
                    await websocket.send_text(token)

            except Exception as e:
                # IMPORTANT: Prevent crash so Phase 6 can run
                print("Streaming error:", e)
                full_ai_response = (
                    "AI response unavailable due to LLM quota or API error."
                )

            # STEP 5B — Save AI message ONCE
            supabase.table("session_events").insert({
                "session_id": session_id,
                "event_type": "ai_message",
                "content": full_ai_response
            }).execute()

            conversation.append({"role": "assistant", "content": full_ai_response})

    # -------------------------------------------------
    # PHASE 6 — Post-Session Summary (ON DISCONNECT)
    # -------------------------------------------------
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")

        # Fetch session events
        events_response = supabase.table("session_events") \
            .select("event_type, content") \
            .eq("session_id", session_id) \
            .order("created_at") \
            .execute()

        events = events_response.data or []

        conversation_text = "\n".join(
            f"{event['event_type']}: {event['content']}"
            for event in events
        )

        summary_prompt = f"""
Summarize the following conversation in 3–4 concise sentences.
Focus on the user's intent and how the AI responded.

Conversation:
{conversation_text}
"""

        # Generate summary (safe fallback)
        try:
            summary_response = await client.responses.create(
                model="gpt-4.1-mini",
                input=summary_prompt
            )
            summary_text = summary_response.output_text

        except Exception as e:
            print("Summary generation error:", e)
            summary_text = (
                "Summary generation failed due to LLM quota or API error."
            )

        # Save end_time + summary
        supabase.table("sessions").update({
            "end_time": datetime.utcnow().isoformat(),
            "summary": summary_text
        }).eq("session_id", session_id).execute()

        print(f"Session ended and summarized: {session_id}")
