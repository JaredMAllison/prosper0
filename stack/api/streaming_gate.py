import queue
import time
from typing import Optional


class StreamingGate:
    """
    Wraps an EnforcementChain and emits tool_call/tool_result events onto a
    thread-safe queue so the async SSE endpoint can forward them to the browser.
    """

    def __init__(self, inner_gate, event_queue: queue.SimpleQueue) -> None:
        self._gate = inner_gate
        self._q = event_queue

    def call(
        self,
        tool_name: str,
        path: Optional[str],
        executor,
        is_transfer: bool = False,
    ) -> bytes:
        self._q.put_nowait({"type": "tool_call", "name": tool_name, "path": path, "args": {}})
        t0 = time.monotonic()
        try:
            result = self._gate.call(tool_name, path, executor, is_transfer)
            ms = int((time.monotonic() - t0) * 1000)
            self._q.put_nowait({
                "type": "tool_result",
                "name": tool_name,
                "ms": ms,
                "bytes": len(result),
                "ok": True,
            })
            return result
        except Exception:
            ms = int((time.monotonic() - t0) * 1000)
            self._q.put_nowait({
                "type": "tool_result",
                "name": tool_name,
                "ms": ms,
                "bytes": 0,
                "ok": False,
            })
            raise
