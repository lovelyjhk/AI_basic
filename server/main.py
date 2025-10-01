from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
import asyncio
from collections import deque
from typing import Deque, Dict, Any, Set
import json
import time
import socket


app = FastAPI(title="RansomShield Demo", version="0.1.0")


class Event(BaseModel):
    event_type: str
    path: str
    host: str = Field(default_factory=lambda: socket.gethostname())
    agent_id: str = "agent-1"
    ts: float = Field(default_factory=lambda: time.time())


# In-memory fan-out to SSE clients
listeners: Set[asyncio.Queue] = set()
recent_events: Deque[Dict[str, Any]] = deque(maxlen=500)


async def broadcast(event: Dict[str, Any]) -> None:
    recent_events.append(event)
    data = json.dumps(event)
    # Copy listeners to avoid mutation during iteration
    for queue in list(listeners):
        try:
            queue.put_nowait(data)
        except asyncio.QueueFull:
            # Drop if a slow client is lagging behind
            pass


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/events")
async def receive_event(event: Event) -> Dict[str, bool]:
    await broadcast(event.model_dump())
    return {"ok": True}


@app.get("/api/recent")
async def get_recent() -> list:
    return list(recent_events)


@app.get("/events")
async def sse(request: Request) -> StreamingResponse:
    queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    listeners.add(queue)

    async def event_stream():
        try:
            # Replay a small history so the dashboard has immediate context
            for ev in list(recent_events)[-50:]:
                yield f"data: {json.dumps(ev)}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            listeners.discard(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>RansomShield Demo</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: #0b1320; color: #e6edf3; }
    header { background: #111a2b; padding: 16px 20px; position: sticky; top: 0; z-index: 10; }
    h1 { margin: 0; font-size: 18px; }
    .container { padding: 16px 20px; }
    .stats { display: flex; gap: 12px; margin-bottom: 16px; }
    .stat { background: #0f1b2d; border: 1px solid #20304a; border-radius: 8px; padding: 10px 12px; }
    .events { background: #0f1b2d; border: 1px solid #20304a; border-radius: 8px; padding: 12px; max-height: 60vh; overflow: auto; }
    .event { padding: 8px; border-bottom: 1px solid #20304a; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \
      \"Liberation Mono\", \"Courier New\", monospace; }
    .event:last-child { border-bottom: none; }
    .ok { color: #3fb950; }
    .warn { color: #d29922; }
    .err { color: #f85149; }
    .muted { color: #9aa7b3; }
    .pill { display: inline-block; padding: 2px 6px; border-radius: 12px; background: #1c2a42; border: 1px solid #2a3f60; font-size: 12px; margin-right: 6px; }
    .footer { margin-top: 10px; font-size: 12px; color: #9aa7b3; }
  </style>
 </head>
 <body>
  <header>
    <h1>🛡️ RansomShield Demo – Live Events</h1>
  </header>
  <div class=\"container\">
    <div class=\"stats\">
      <div class=\"stat\">System: <span id=\"status\" class=\"ok\">OK</span></div>
      <div class=\"stat\">Events: <span id=\"count\">0</span></div>
      <div class=\"stat\">Stream: <span id=\"stream\" class=\"muted\">connecting…</span></div>
    </div>
    <div class=\"events\" id=\"events\"></div>
    <div class=\"footer\">Open a terminal to run the simulator to generate file changes.</div>
  </div>
  <script>
    const eventsEl = document.getElementById('events');
    const countEl = document.getElementById('count');
    const streamEl = document.getElementById('stream');
    let count = 0;
    function addEvent(ev) {
      count += 1; countEl.textContent = count;
      const div = document.createElement('div');
      div.className = 'event';
      const t = new Date((ev.ts || 0) * 1000).toLocaleTimeString();
      div.innerHTML = `<span class=\"pill\">${ev.event_type}</span><strong>${ev.path}</strong><br/><span class=\"muted\">${ev.agent_id} • ${ev.host} • ${t}</span>`;
      eventsEl.prepend(div);
    }
    async function ping() {
      try { const r = await fetch('/health'); const j = await r.json(); document.getElementById('status').textContent = j.status === 'ok' ? 'OK' : 'WARN'; }
      catch (e) { document.getElementById('status').textContent = 'DOWN'; document.getElementById('status').className = 'err'; }
    }
    ping(); setInterval(ping, 5000);
    const es = new EventSource('/events');
    es.onopen = () => { streamEl.textContent = 'connected'; streamEl.className = 'ok'; };
    es.onerror = () => { streamEl.textContent = 'disconnected'; streamEl.className = 'err'; };
    es.onmessage = (msg) => {
      try { const ev = JSON.parse(msg.data); addEvent(ev); } catch (e) { /* ignore */ }
    };
  </script>
 </body>
 </html>
    """

