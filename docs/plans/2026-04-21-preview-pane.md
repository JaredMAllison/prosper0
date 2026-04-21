# Preview Pane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Preview pane as the 2nd column (Chat | Preview | Stack | Audit) that shows file contents on reads and blocks pending writes for operator confirmation before executing.

**Architecture:** The `StreamingGate` is instrumented to emit `file_read` and `write_proposed` SSE events. Write calls block on a `threading.Event` stored in a per-session registry; `POST /v1/confirm-write` and `/v1/reject-write` resolve the event from the browser. The PreviewPane renders the file or diff and exposes Approve/Discard buttons.

**Tech Stack:** Python threading.Event (write gate), FastAPI (two new endpoints), React JSX (new PreviewPane component), CSS grid (4-column workspace layout)

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `stack/orchestrator/loop.py` | Pass `args=tc.arguments` to `gate.call()` |
| Modify | `stack/mcp/definitions.py` | No change needed — tool names confirmed: `read_file`, `write_file` |
| Create | `stack/api/write_gate.py` | Thread-safe registry of pending write confirmations |
| Modify | `stack/api/streaming_gate.py` | Accept `args`, emit `file_read` + `write_proposed`, block writes |
| Modify | `stack/api/server.py` | Add confirm/reject endpoints; pass `session_id` to `StreamingGate` |
| Create | `console/src/preview.jsx` | PreviewPane component + PREVIEW_CSS |
| Modify | `console/styles.css` | 4-column workspace grid with `data-preview` attribute |
| Modify | `console/src/app.jsx` | Preview state, SSE handlers, confirm/reject fetch, pane wiring |
| Modify | `console/Prosper0 Operator Console.html` | Add `<script src="src/preview.jsx">` before app.jsx |

---

## Task 1: Extend `GateCaller` protocol and `loop.py`

**Files:**
- Modify: `stack/orchestrator/loop.py`

The gate's `call()` currently has no access to the full arguments dict. We need it for write previews. This is a minimal, backward-compatible change — `args` defaults to `None`.

- [ ] **Step 1: Update `GateCaller` protocol in `loop.py`**

```python
# stack/orchestrator/loop.py  — update GateCaller only
@runtime_checkable
class GateCaller(Protocol):
    def call(
        self,
        tool_name: str,
        path: Optional[str],
        executor: Callable[[], bytes],
        is_transfer: bool = False,
        args: Optional[dict] = None,
    ) -> bytes: ...
```

- [ ] **Step 2: Pass `args` in the `run()` loop**

```python
# Inside run(), replace the gate.call() invocation:
result = gate.call(
    tool_name=tc.name,
    path=tc.arguments.get("path"),
    executor=lambda: tool_executor(tc.name, tc.arguments),
    args=tc.arguments,          # ← new
)
```

- [ ] **Step 3: Run existing tests to confirm nothing broke**

```bash
cd /home/jared/prosper0
pytest tests/ -v --ignore=tests/smoke -q
```

Expected: all tests pass (the `_NoOpGate` in `main.py` already accepts `**kwargs` implicitly via Python duck typing — if it doesn't, you'll see a TypeError and need to add `args=None` to its `call()` signature).

- [ ] **Step 4: If tests fail on `_NoOpGate`, fix it**

```python
# stack/orchestrator/main.py — _NoOpGate
class _NoOpGate:
    def call(self, tool_name, path, executor, is_transfer=False, args=None):
        return executor()
```

- [ ] **Step 5: Also fix `_NoOpGate` in `stack/api/server.py`**

```python
# stack/api/server.py — _NoOpGate
class _NoOpGate:
    def call(self, tool_name, path, executor, is_transfer=False, args=None):
        return executor()
```

- [ ] **Step 6: Run tests again, confirm green**

```bash
pytest tests/ -v --ignore=tests/smoke -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add stack/orchestrator/loop.py stack/orchestrator/main.py stack/api/server.py
git commit -m "feat: pass args dict through GateCaller.call() for write preview"
```

---

## Task 2: Write gate registry

**Files:**
- Create: `stack/api/write_gate.py`
- Test: `tests/api/test_write_gate.py`

Thread-safe dict of pending write confirmations. Each entry is keyed by `session_id` and holds a `threading.Event` plus the decision.

- [ ] **Step 1: Create the test directory**

```bash
touch tests/api/__init__.py
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/api/test_write_gate.py
import threading
from stack.api.write_gate import register, resolve, get, PendingWrite


def test_register_creates_entry():
    pw = register("sess1", "/vault/test.md", "hello world")
    assert get("sess1") is pw
    assert pw.path == "/vault/test.md"
    assert pw.proposed_content == "hello world"
    assert not pw.event.is_set()
    assert pw.approved is False


def test_resolve_approve_signals_event():
    register("sess2", "/vault/x.md", "content")
    ok = resolve("sess2", approved=True)
    assert ok is True
    pw = get("sess2")
    assert pw is None          # removed from registry after resolve


def test_resolve_approve_sets_flag():
    pw = register("sess3", "/vault/y.md", "body")
    # Run resolve in a thread to simulate the HTTP endpoint
    t = threading.Thread(target=resolve, args=("sess3", True))
    t.start()
    pw.event.wait(timeout=1)
    t.join()
    assert pw.approved is True
    assert pw.event.is_set()


def test_resolve_reject_sets_flag():
    pw = register("sess4", "/vault/z.md", "body")
    resolve("sess4", approved=False)
    assert pw.approved is False


def test_resolve_unknown_session_returns_false():
    assert resolve("does-not-exist", approved=True) is False
```

- [ ] **Step 3: Run to confirm they fail**

```bash
pytest tests/api/test_write_gate.py -v
```

Expected: `ModuleNotFoundError: No module named 'stack.api.write_gate'`

- [ ] **Step 4: Implement `write_gate.py`**

```python
# stack/api/write_gate.py
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PendingWrite:
    path: str
    proposed_content: str
    event: threading.Event = field(default_factory=threading.Event)
    approved: bool = False


_registry: dict[str, PendingWrite] = {}
_lock = threading.Lock()


def register(session_id: str, path: str, proposed_content: str) -> PendingWrite:
    pw = PendingWrite(path=path, proposed_content=proposed_content)
    with _lock:
        _registry[session_id] = pw
    return pw


def resolve(session_id: str, approved: bool) -> bool:
    with _lock:
        pw = _registry.pop(session_id, None)
    if pw is None:
        return False
    pw.approved = approved
    pw.event.set()
    return True


def get(session_id: str) -> Optional[PendingWrite]:
    with _lock:
        return _registry.get(session_id)
```

- [ ] **Step 5: Run tests, confirm green**

```bash
pytest tests/api/test_write_gate.py -v
```

Expected: 5 tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/api/__init__.py stack/api/write_gate.py tests/api/test_write_gate.py
git commit -m "feat: add write gate registry for operator-gated writes"
```

---

## Task 3: Update `StreamingGate` to emit file events and block writes

**Files:**
- Modify: `stack/api/streaming_gate.py`
- Test: `tests/api/test_streaming_gate.py`

The gate now:
- Emits `{type: "file_read", path, content}` after a successful `read_file`
- For `write_file`: emits `{type: "write_proposed", path, proposed_content, session_id}`, blocks until resolved, raises on rejection

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/test_streaming_gate.py
import queue
import threading
import time
from unittest.mock import MagicMock
from stack.api.streaming_gate import StreamingGate
import stack.api.write_gate as wg


def _make_gate(session_id="test-sess"):
    q = queue.SimpleQueue()
    inner = MagicMock()
    inner.call.return_value = b"file contents"
    gate = StreamingGate(inner, q, session_id=session_id)
    return gate, inner, q


def _drain(q):
    items = []
    try:
        while True:
            items.append(q.get_nowait())
    except queue.Empty:
        pass
    return items


def test_read_emits_tool_call_result_and_file_read():
    gate, inner, q = _make_gate()
    gate.call("read_file", "/vault/note.md", lambda: b"file contents",
              args={"path": "/vault/note.md"})
    events = _drain(q)
    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    assert "file_read" in types
    fr = next(e for e in events if e["type"] == "file_read")
    assert fr["path"] == "/vault/note.md"
    assert fr["content"] == "file contents"


def test_write_emits_write_proposed_and_blocks():
    gate, inner, q = _make_gate(session_id="write-sess")
    approved_at = {}

    def approve():
        import time; time.sleep(0.05)
        approved_at["t"] = time.monotonic()
        wg.resolve("write-sess", approved=True)

    threading.Thread(target=approve, daemon=True).start()
    started_at = time.monotonic()
    gate.call("write_file", "/vault/new.md", lambda: b"",
              args={"path": "/vault/new.md", "content": "hello"})
    completed_at = time.monotonic()

    # Gate must have blocked: inner.call should not have been reached
    # until after resolve() fired (i.e. at least 50ms elapsed).
    assert completed_at - started_at >= 0.04, "gate did not block waiting for approval"
    # inner.call was invoked exactly once (after approval)
    inner.call.assert_called_once()

    events = _drain(q)
    types = [e["type"] for e in events]
    assert "write_proposed" in types
    wp = next(e for e in events if e["type"] == "write_proposed")
    assert wp["path"] == "/vault/new.md"
    assert wp["proposed_content"] == "hello"
    assert wp["session_id"] == "write-sess"


def test_write_rejected_raises():
    gate, inner, q = _make_gate(session_id="reject-sess")
    def reject():
        import time; time.sleep(0.05)
        wg.resolve("reject-sess", approved=False)
    threading.Thread(target=reject, daemon=True).start()

    import pytest
    with pytest.raises(PermissionError, match="rejected"):
        gate.call("write_file", "/vault/bad.md", lambda: b"",
                  args={"path": "/vault/bad.md", "content": "evil"})


def test_write_timeout_raises():
    gate, inner, q = _make_gate(session_id="timeout-sess")
    import pytest
    with pytest.raises(TimeoutError):
        gate.call("write_file", "/vault/slow.md", lambda: b"",
                  args={"path": "/vault/slow.md", "content": "x"},
                  _write_timeout=0.01)   # tiny timeout for test speed
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/api/test_streaming_gate.py -v
```

Expected: ImportError or failures.

- [ ] **Step 3: Rewrite `streaming_gate.py`**

```python
# stack/api/streaming_gate.py
import queue
import time
from typing import Optional
from stack.api import write_gate

WRITE_TOOLS = {"write_file"}
READ_TOOLS = {"read_file"}
DEFAULT_WRITE_TIMEOUT = 120  # seconds; operator has 2 minutes to respond


class StreamingGate:
    def __init__(self, inner_gate, event_queue: queue.SimpleQueue, session_id: str) -> None:
        self._gate = inner_gate
        self._q = event_queue
        self._session_id = session_id

    def call(
        self,
        tool_name: str,
        path: Optional[str],
        executor,
        is_transfer: bool = False,
        args: Optional[dict] = None,
        _write_timeout: float = DEFAULT_WRITE_TIMEOUT,
    ) -> bytes:
        self._q.put_nowait({"type": "tool_call", "name": tool_name, "path": path, "args": args or {}})

        if tool_name in WRITE_TOOLS:
            proposed = (args or {}).get("content", "")
            pw = write_gate.register(self._session_id, path or "", proposed)
            self._q.put_nowait({
                "type": "write_proposed",
                "path": path,
                "proposed_content": proposed,
                "session_id": self._session_id,
            })
            if not pw.event.wait(timeout=_write_timeout):
                write_gate.resolve(self._session_id, approved=False)
                raise TimeoutError(f"Write to {path} timed out waiting for operator confirmation")
            if not pw.approved:
                raise PermissionError(f"Write to {path} rejected by operator")

        t0 = time.monotonic()
        try:
            result = self._gate.call(tool_name, path, executor, is_transfer)
        except Exception:
            ms = int((time.monotonic() - t0) * 1000)
            self._q.put_nowait({"type": "tool_result", "name": tool_name, "ms": ms, "bytes": 0, "ok": False})
            raise

        ms = int((time.monotonic() - t0) * 1000)
        self._q.put_nowait({"type": "tool_result", "name": tool_name, "ms": ms, "bytes": len(result), "ok": True})

        if tool_name in READ_TOOLS:
            self._q.put_nowait({
                "type": "file_read",
                "path": path,
                "content": result.decode("utf-8", errors="replace"),
            })

        return result
```

- [ ] **Step 4: Run tests, confirm green**

```bash
pytest tests/api/test_streaming_gate.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add stack/api/streaming_gate.py tests/api/test_streaming_gate.py
git commit -m "feat: streaming gate emits file_read, blocks write_file pending approval"
```

---

## Task 4: Add confirm/reject endpoints to `server.py`

**Files:**
- Modify: `stack/api/server.py`

Two new endpoints. Also update `_build_stack` to thread `session_id` into `StreamingGate`.

- [ ] **Step 1: Update `StreamingGate` instantiation in `/v1/turn`**

In `server.py`, the `turn()` endpoint currently does:
```python
gate = StreamingGate(inner_gate, event_q)
```

Replace with:
```python
gate = StreamingGate(inner_gate, event_q, session_id=session_id)
```

(The `session_id` variable already exists in that function.)

- [ ] **Step 2: Add the two new endpoints to `server.py`**

Add after the `/v1/mode` endpoints:

```python
# --- POST /v1/confirm-write/{session_id} ---
@app.post("/v1/confirm-write/{session_id}")
async def confirm_write(session_id: str):
    from stack.api import write_gate
    ok = write_gate.resolve(session_id, approved=True)
    if not ok:
        return JSONResponse(status_code=404, content={"error": "no pending write for this session"})
    return {"approved": True}


# --- POST /v1/reject-write/{session_id} ---
@app.post("/v1/reject-write/{session_id}")
async def reject_write(session_id: str):
    from stack.api import write_gate
    ok = write_gate.resolve(session_id, approved=False)
    if not ok:
        return JSONResponse(status_code=404, content={"error": "no pending write for this session"})
    return {"approved": False}
```

- [ ] **Step 3: Run existing tests to confirm no regressions**

```bash
pytest tests/ -v --ignore=tests/smoke -q
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add stack/api/server.py
git commit -m "feat: add /v1/confirm-write and /v1/reject-write endpoints"
```

---

## Task 5: PreviewPane component

**Files:**
- Create: `console/src/preview.jsx`

A new pane with three states: `idle` (shows placeholder), `reading` (shows file content), `write_pending` (shows proposed content + Approve/Discard).

- [ ] **Step 1: Create `console/src/preview.jsx`**

```jsx
/* global React, StatusDot, Chip, cx */
// Preview pane: shows file content on reads, proposed writes for confirmation.
// Exposed API: window.P0.PreviewPane = PreviewPane

const { useState, useEffect, useRef } = React;

function PreviewPane({ preview, onApprove, onDiscard, onCollapse }) {
  const bodyRef = useRef(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = 0;
  }, [preview?.path]);

  if (!preview) {
    return (
      <div className="pane preview-pane">
        <PreviewHead label="preview · file viewer" onCollapse={onCollapse} />
        <div className="pane-body preview-idle mono xs dim">
          <span>no file selected · reads and proposed writes appear here</span>
        </div>
      </div>
    );
  }

  const { kind, path, content, proposed_content, session_id } = preview;
  const isPending = kind === "write_proposed";

  return (
    <div className="pane preview-pane">
      <PreviewHead
        label={isPending ? "preview · write pending" : "preview · reading"}
        status={isPending ? "warn" : "info"}
        path={path}
        onCollapse={onCollapse}
      />

      <div className="pane-body preview-body" ref={bodyRef}>
        {isPending && (
          <div className="preview-write-banner mono xxs">
            <StatusDot status="warn" />
            <span className="warn-text">ariel wants to write this file · approve or discard</span>
          </div>
        )}

        <div className="preview-path-bar mono xxs dim">{path}</div>

        {isPending ? (
          <div className="preview-split">
            <div className="preview-half">
              <div className="preview-half-label mono xxs dim caps">current · on disk</div>
              <pre className="preview-code">{content || "(new file)"}</pre>
            </div>
            <div className="preview-half preview-half-proposed">
              <div className="preview-half-label mono xxs warn-text caps">proposed · ariel</div>
              <pre className="preview-code">{proposed_content}</pre>
            </div>
          </div>
        ) : (
          <pre className="preview-code">{content}</pre>
        )}
      </div>

      {isPending && (
        <div className="preview-actions">
          <div className="mono xxs dim">operator gate · ai cannot write without you</div>
          <div className="preview-action-buttons">
            <button className="btn-primary mono" onClick={() => onApprove(session_id)}>
              approve write
            </button>
            <button className="btn-ghost mono" onClick={() => onDiscard(session_id)}>
              discard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PreviewHead({ label, status = "info", path, onCollapse }) {
  return (
    <div className="pane-head">
      <div className="left">
        <span>{label}</span>
        {path && (
          <Chip tone="" style={{ padding: "1px 6px", maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis" }}>
            <span className="mono" title={path}>{path.split("/").pop()}</span>
          </Chip>
        )}
      </div>
      <div className="right">
        {status && <StatusDot status={status} />}
        {onCollapse && (
          <button className="pane-collapse" onClick={onCollapse} title="minimize preview">×</button>
        )}
      </div>
    </div>
  );
}

const PREVIEW_CSS = `
.preview-pane { background: var(--bg-1); }
.preview-idle {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px;
  text-align: center;
  line-height: 1.6;
}
.preview-body { padding: 0; display: flex; flex-direction: column; }
.preview-write-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--warn-dim);
  border-bottom: 1px solid color-mix(in oklch, var(--warn) 30%, var(--line));
}
.warn-text { color: var(--warn); }
.preview-path-bar {
  padding: 6px 12px;
  border-bottom: 1px solid var(--line-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.preview-code {
  margin: 0;
  padding: 12px;
  font-family: var(--mono);
  font-size: var(--fs-xs);
  line-height: 1.55;
  color: var(--fg-1);
  white-space: pre-wrap;
  word-break: break-word;
  flex: 1 1 auto;
}
.preview-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  flex: 1 1 auto;
  min-height: 0;
}
.preview-half { display: flex; flex-direction: column; overflow: auto; }
.preview-half + .preview-half { border-left: 1px solid var(--line); }
.preview-half-proposed { background: color-mix(in oklch, var(--warn) 4%, var(--bg-1)); }
.preview-half-label {
  padding: 4px 12px;
  border-bottom: 1px dashed var(--line-soft);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.preview-actions {
  flex: 0 0 auto;
  border-top: 1px solid var(--line);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--bg-2);
}
.preview-action-buttons { display: flex; gap: 8px; }
`;

Object.assign(window, { PreviewPane, PREVIEW_CSS });
```

- [ ] **Step 2: Verify the file was created**

```bash
wc -l /home/jared/prosper0/console/src/preview.jsx
```

Expected: ~130+ lines.

- [ ] **Step 3: Commit**

```bash
git add console/src/preview.jsx
git commit -m "feat: add PreviewPane component with read/write-pending states"
```

---

## Task 6: Update CSS grid for 4-column layout

**Files:**
- Modify: `console/styles.css` (lines 225–238)

Add `data-preview` to the workspace grid. The pane order in the DOM will be: Chat, Preview, Stack, Audit. Eight selector combinations (2³).

- [ ] **Step 1: Replace the workspace grid block in `styles.css`**

Find and replace lines 225–238 (the comment through the last `.workspace[...]` selector):

```css
/* Four-column grid: Chat | Preview | Stack | Audit */
.workspace {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(340px, 0.9fr) minmax(380px, 1.1fr) minmax(280px, 0.75fr);
  gap: 0;
  height: 100%;
  min-height: 0;
  border-top: 1px solid var(--line);
  transition: grid-template-columns 0.22s ease;
}

/* All open */
.workspace[data-preview="open"][data-stack="open"][data-audit="open"] {
  grid-template-columns: minmax(320px, 1fr) minmax(340px, 0.9fr) minmax(380px, 1.1fr) minmax(280px, 0.75fr);
}
/* Preview closed */
.workspace[data-preview="closed"][data-stack="open"][data-audit="open"] {
  grid-template-columns: minmax(360px, 1fr) 34px minmax(440px, 1.3fr) minmax(320px, 0.8fr);
}
/* Stack closed */
.workspace[data-preview="open"][data-stack="closed"][data-audit="open"] {
  grid-template-columns: minmax(300px, 1fr) minmax(320px, 0.9fr) 34px minmax(280px, 0.75fr);
}
/* Audit closed */
.workspace[data-preview="open"][data-stack="open"][data-audit="closed"] {
  grid-template-columns: minmax(300px, 1fr) minmax(320px, 0.9fr) minmax(400px, 1.3fr) 34px;
}
/* Preview + Stack closed */
.workspace[data-preview="closed"][data-stack="closed"][data-audit="open"] {
  grid-template-columns: minmax(0, 1fr) 34px 34px minmax(280px, 0.75fr);
}
/* Preview + Audit closed */
.workspace[data-preview="closed"][data-stack="open"][data-audit="closed"] {
  grid-template-columns: minmax(320px, 0.8fr) 34px minmax(0, 1fr) 34px;
}
/* Stack + Audit closed */
.workspace[data-preview="open"][data-stack="closed"][data-audit="closed"] {
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr) 34px 34px;
}
/* All closed */
.workspace[data-preview="closed"][data-stack="closed"][data-audit="closed"] {
  grid-template-columns: minmax(0, 1fr) 34px 34px 34px;
}
```

- [ ] **Step 2: Commit**

```bash
git add console/styles.css
git commit -m "feat: expand workspace to 4-column grid for preview pane"
```

---

## Task 7: Wire PreviewPane into `app.jsx`

**Files:**
- Modify: `console/src/app.jsx`

Add `previewOpen` and `preview` state, handle new SSE events, wire confirm/reject.

- [ ] **Step 1: Add state declarations**

In `App()`, after the existing `useState` calls, add:

```jsx
const [previewOpen, setPreviewOpen] = useState(true);
const [preview, setPreview] = useState(null);
// preview shape: { kind: "file_read"|"write_proposed", path, content,
//                  proposed_content, session_id } | null
```

Also add `previewOpen` persistence (mirrors the existing pattern for stackOpen/auditOpen):

```jsx
const [previewOpen, setPreviewOpen] = useState(() => {
  const v = localStorage.getItem("p0.previewOpen"); return v === null ? true : v === "1";
});
useEffect(() => { localStorage.setItem("p0.previewOpen", previewOpen ? "1" : "0"); }, [previewOpen]);
```

- [ ] **Step 2: Add `file_read` and `write_proposed` handlers inside `handleSubmit`**

Inside the SSE event dispatch loop in `handleSubmit`, add two new `else if` branches before the `"end"` check:

```jsx
} else if (payload.type === "file_read") {
  setPreviewOpen(true);
  setPreview({
    kind: "file_read",
    path: payload.path,
    content: payload.content,
    proposed_content: null,
    session_id: null,
  });
} else if (payload.type === "write_proposed") {
  setPreviewOpen(true);
  setPreview({
    kind: "write_proposed",
    path: payload.path,
    content: null,           // current disk content unknown; server could add this later
    proposed_content: payload.proposed_content,
    session_id: payload.session_id,
  });
}
```

- [ ] **Step 3: Add confirm/reject callbacks**

Add these two functions inside `App()` after `handleModeChange`:

```jsx
const handleApproveWrite = useCallback((sessionId) => {
  fetch(`${API_BASE}/v1/confirm-write/${sessionId}`, { method: "POST" })
    .catch(() => {});
  setPreview(prev => prev?.session_id === sessionId
    ? { ...prev, kind: "file_read", proposed_content: null }
    : prev);
}, []);

const handleDiscardWrite = useCallback((sessionId) => {
  fetch(`${API_BASE}/v1/reject-write/${sessionId}`, { method: "POST" })
    .catch(() => {});
  setPreview(null);
}, []);
```

- [ ] **Step 4: Update the workspace JSX**

Replace the existing `<div className="workspace" ...>` block with the 4-pane version. The new workspace has `data-preview` and renders `PreviewPane` as the 2nd child (after `ChatPane`):

```jsx
<div
  className="workspace"
  data-preview={previewOpen ? "open" : "closed"}
  data-stack={stackOpen ? "open" : "closed"}
  data-audit={auditOpen ? "open" : "closed"}
>
  <ChatPane
    turns={turns}
    onSubmit={handleSubmit}
    streaming={streaming}
    mode={mode}
  />
  {previewOpen ? (
    <PreviewPane
      preview={preview}
      onApprove={handleApproveWrite}
      onDiscard={handleDiscardWrite}
      onCollapse={() => setPreviewOpen(false)}
    />
  ) : (
    <CollapsedRail
      label="preview"
      sub={preview?.kind === "write_proposed" ? "write pending" : "file viewer"}
      badge={preview?.kind === "write_proposed" ? "⚠ pending" : undefined}
      onExpand={() => setPreviewOpen(true)}
    />
  )}
  {stackOpen ? (
    <StackPane
      layers={window.P0.LAYERS}
      focusedId={focusedId}
      setFocusedId={setFocusedId}
      tools={window.P0.TOOLS}
      audit={audit}
      onCollapse={() => setStackOpen(false)}
    />
  ) : (
    <CollapsedRail
      label="stack"
      sub="six layers"
      badge={window.P0.LAYERS.filter(l => l.status === "nominal").length + " online"}
      onExpand={() => setStackOpen(true)}
    />
  )}
  {auditOpen ? (
    <AuditPane
      events={audit}
      verbosity={tweaks.values.auditVerbosity}
      onCollapse={() => setAuditOpen(false)}
    />
  ) : (
    <CollapsedRail
      label="audit"
      sub="transparency"
      badge={audit.length + " events"}
      onExpand={() => setAuditOpen(true)}
      side="right"
    />
  )}
</div>
```

- [ ] **Step 5: Add PREVIEW_CSS to the style injection at bottom of App()**

```jsx
<style>{HEADER_CSS + STACK_CSS + CHAT_CSS + AUDIT_CSS + FOOTER_CSS + PREVIEW_CSS}</style>
```

- [ ] **Step 6: Commit**

```bash
git add console/src/app.jsx
git commit -m "feat: wire PreviewPane into app — file_read and write_proposed SSE events"
```

---

## Task 8: Add `preview.jsx` to the HTML loader

**Files:**
- Modify: `console/Prosper0 Operator Console.html`

The HTML loads scripts in dependency order. `preview.jsx` depends on atoms (for `StatusDot`, `Chip`, `cx`) and must load before `app.jsx`.

- [ ] **Step 1: Add the script tag**

Insert after `src/audit.jsx` and before `src/tweaks.jsx`:

```html
  <script type="text/babel" src="src/audit.jsx"></script>
  <script type="text/babel" src="src/preview.jsx"></script>   <!-- ← add this line -->
  <script type="text/babel" src="src/footer.jsx"></script>
```

- [ ] **Step 2: Commit**

```bash
git add "console/Prosper0 Operator Console.html"
git commit -m "feat: load preview.jsx in operator console"
```

---

## Verification

1. Install new deps: `pip install -e .` in the prosper0 repo
2. Start the API server locally: `VAULT_PATH=./deploy/vault TOOLS_CONFIG_PATH=./stack/tools.config.yaml AUDIT_LOG_PATH=./deploy/logs python -m uvicorn stack.api.server:app --reload --port 8080`
3. Open `http://localhost:8080` — confirm 4-pane layout renders with Preview as 2nd column
4. Send a message that triggers a `read_file` tool call — confirm Preview pane populates with file content
5. Send a message that triggers a `write_file` — confirm Preview shows split view with Approve/Discard buttons, and the agent loop is visibly blocked (streaming indicator stays on)
6. Click **Approve** — confirm the write completes, streaming ends, audit log updates
7. Click **Discard** on a second write — confirm the loop receives rejection, Ariel responds with an error message
8. Collapse the Preview pane — confirm it folds to a 34px rail; badge shows "⚠ pending" when a write is blocked
9. Run full test suite: `pytest tests/ --ignore=tests/smoke -q`
