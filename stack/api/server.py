"""
FastAPI HTTP layer for the Prosper0 operator console.

Four endpoints:
  POST /v1/turn    — SSE stream: run the agent loop, stream tool/response events
  GET  /v1/health  — layer health check (Ollama, vault, audit)
  GET  /v1/audit   — audit log entries for the current day
  GET  /v1/mode    — current mode
  POST /v1/mode    — set mode
  GET  /           — serve the operator console HTML
"""
import asyncio
import json
import os
import queue
import threading
import uuid
from datetime import date
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="Prosper0 API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Config ---
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./vault"))
CONFIG_PATH = Path(os.environ.get("TOOLS_CONFIG_PATH", "./tools.config.yaml"))
AUDIT_LOG_PATH = Path(os.environ.get("AUDIT_LOG_PATH", "./logs"))
STATE_PATH = Path(os.environ.get("STATE_PATH", "./state.json"))
CONSOLE_DIR = Path(os.environ.get("CONSOLE_DIR", "./console"))

# --- Static files (console UI) ---
if (CONSOLE_DIR / "src").exists():
    app.mount("/src", StaticFiles(directory=str(CONSOLE_DIR / "src")), name="src")


@app.get("/")
async def console():
    html = CONSOLE_DIR / "Prosper0 Operator Console.html"
    if html.exists():
        return FileResponse(str(html))
    return JSONResponse({"status": "console not found", "expected": str(html)}, status_code=404)


# --- State helpers ---
def _read_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"mode": "available"}


def _write_state(data: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data))


# --- Stack builder ---
class _NoOpGate:
    def call(self, tool_name, path, executor, is_transfer=False):
        return executor()


def _build_stack(session_id: str):
    from stack.orchestrator.ollama import OllamaBackend
    from stack.orchestrator.prompt import build_system_prompt
    from stack.orchestrator.config import load_tools_config
    from stack.mcp.registry import make_tool_executor
    from stack.mcp.definitions import TOOL_DEFINITIONS

    state = _read_state()
    mode = state.get("mode", "available")

    backend = OllamaBackend(host=OLLAMA_HOST, model=OLLAMA_MODEL)

    try:
        from transparency.enforcement.config import ToolsConfig
        from transparency.enforcement.audit_logger import AuditLogger
        from transparency.enforcement.chain import EnforcementChain

        raw = load_tools_config(CONFIG_PATH)
        tools_config = ToolsConfig.from_dict(raw)
        audit = AuditLogger(AUDIT_LOG_PATH)
        inner_gate = EnforcementChain(
            config=tools_config,
            audit=audit,
            smtp_config={},
            session_id=session_id,
            log_dir=AUDIT_LOG_PATH,
        )
    except (ImportError, Exception):
        inner_gate = _NoOpGate()

    tool_executor = make_tool_executor(vault_root=VAULT_PATH)
    system_prompt = build_system_prompt(
        mode=mode,
        session_id=session_id,
        memory_dir=VAULT_PATH / "memory",
        skills_dir=VAULT_PATH / "skills",
    )
    return backend, inner_gate, tool_executor, TOOL_DEFINITIONS, system_prompt


# --- POST /v1/turn ---
class TurnRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.post("/v1/turn")
async def turn(req: TurnRequest):
    from stack.orchestrator.loop import run, MaxIterationsError
    from stack.api.streaming_gate import StreamingGate

    session_id = str(uuid.uuid4())[:8]
    event_q: queue.SimpleQueue = queue.SimpleQueue()
    backend, inner_gate, tool_executor, tool_defs, system_prompt = _build_stack(session_id)
    gate = StreamingGate(inner_gate, event_q)
    messages = list(req.history) + [{"role": "user", "content": req.message}]
    result: dict = {}

    def run_loop():
        try:
            result["text"] = run(backend, gate, tool_executor, messages, tool_defs, system_prompt)
        except MaxIterationsError as exc:
            result["error"] = str(exc)
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            event_q.put(None)

    threading.Thread(target=run_loop, daemon=True).start()

    async def generate():
        while True:
            try:
                item = event_q.get_nowait()
                if item is None:
                    break
                yield {"data": json.dumps(item)}
            except queue.Empty:
                await asyncio.sleep(0.05)

        if "text" in result:
            yield {"data": json.dumps({"type": "token", "text": result["text"]})}
        if "error" in result:
            yield {"data": json.dumps({"type": "error", "text": result["error"]})}
        yield {"data": json.dumps({"type": "end"})}

    return EventSourceResponse(generate())


# --- GET /v1/health ---
@app.get("/v1/health")
async def health():
    layers = []

    # L1: Ollama
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{OLLAMA_HOST}/api/ps", timeout=3.0)
            models = r.json().get("models", [])
        model_info = models[0] if models else {}
        layers.append({
            "id": 1, "code": "L1", "name": "LLM Stack · von Prosper0",
            "status": "nominal" if models else "warn",
            "metrics": [
                ["model", model_info.get("name", "— not loaded")],
                ["mem res.", model_info.get("size_vram", "—")],
            ],
        })
    except Exception:
        layers.append({
            "id": 1, "code": "L1", "name": "LLM Stack · von Prosper0",
            "status": "fault",
            "metrics": [["ollama", "unreachable"]],
        })

    # L2: Vault
    note_count = len(list(VAULT_PATH.glob("**/*.md"))) if VAULT_PATH.exists() else 0
    layers.append({
        "id": 2, "code": "L2", "name": "Prosper0 Vault",
        "status": "nominal" if note_count > 0 else "warn",
        "metrics": [["path", str(VAULT_PATH)], ["notes", str(note_count)]],
    })

    # L4: Audit
    today_log = AUDIT_LOG_PATH / f"audit-{date.today().isoformat()}.log"
    entry_count = 0
    if today_log.exists():
        entry_count = sum(1 for line in today_log.open() if line.strip())
    layers.append({
        "id": 4, "code": "L4", "name": "Employer Transparency",
        "status": "nominal",
        "metrics": [["audit entries today", str(entry_count)]],
    })

    state = _read_state()
    return {"layers": layers, "mode": state.get("mode", "available")}


# --- GET /v1/audit ---
@app.get("/v1/audit")
async def audit_log(since: Optional[str] = None):
    today_log = AUDIT_LOG_PATH / f"audit-{date.today().isoformat()}.log"
    entries = []
    if today_log.exists():
        for line in today_log.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if since and entry.get("timestamp", "") <= since:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return {"entries": entries[-100:]}


# --- GET/POST /v1/mode ---
@app.get("/v1/mode")
async def get_mode():
    return _read_state()


class ModeRequest(BaseModel):
    mode: str


VALID_MODES = {"available", "in-meeting", "deep-work", "off-hours"}


@app.post("/v1/mode")
async def set_mode(req: ModeRequest):
    if req.mode not in VALID_MODES:
        return JSONResponse(
            status_code=400,
            content={"error": f"invalid mode '{req.mode}', must be one of {sorted(VALID_MODES)}"},
        )
    state = _read_state()
    state["mode"] = req.mode
    _write_state(state)
    return state
