/* global React, ReactDOM, Header, StackPane, ChatPane, AuditPane, Footer,
          useTweaks, TweaksPanel, HEADER_CSS, STACK_CSS, CHAT_CSS, AUDIT_CSS, FOOTER_CSS */

// Point at the FastAPI server. Empty string = same origin (served by prosper0-api).
const API_BASE = window.location.hostname === "localhost" || window.location.hostname === ""
  ? "http://localhost:8080"
  : `http://${window.location.hostname}:8080`;

// Map raw audit JSONL entries to the shape the AuditPane expects.
function normalizeAuditEntries(raw) {
  return raw.map((e, i) => ({
    id: e.timestamp + "-" + i,
    t: e.timestamp ? e.timestamp.slice(11, 23) : "—",
    layer: e.tool?.startsWith("vault") ? 2 : e.tool?.startsWith("transfer") ? 3 : 1,
    kind: e.event === "tool_rejected" ? "deny" : e.event === "tool_attempt" ? "tool" : "tool",
    verb: e.tool || e.event || "—",
    target: e.path || e.content_hash || "—",
    ok: e.event !== "tool_rejected",
    dur: 0,
    note: e.reason || e.outcome || undefined,
  }));
}

function CollapsedRail({ label, sub, badge, onExpand, side = "left" }) {
  return (
    <button className="rail" onClick={onExpand} title={`expand ${label}`}>
      <span className="rail-caret">{side === "right" ? "‹" : "›"}</span>
      <span className="rail-label">{label}</span>
      <span className="rail-sub">{sub}</span>
      {badge && <span className="rail-badge">{badge}</span>}
    </button>
  );
}

const { useState, useCallback, useEffect } = React;

function App() {
  const tweaks = useTweaks();

  const [mode, setMode] = useState("available");
  const [focusedId, setFocusedId] = useState(1); // L1 LLM Stack — active
  const [turns, setTurns]   = useState(window.P0.INITIAL_TURNS);
  const [audit, setAudit]   = useState(window.P0.INITIAL_AUDIT);
  const [streaming, setStreaming] = useState(null);

  // Persisted pane visibility
  const [stackOpen, setStackOpen] = useState(() => {
    const v = localStorage.getItem("p0.stackOpen"); return v === null ? true : v === "1";
  });
  const [auditOpen, setAuditOpen] = useState(() => {
    const v = localStorage.getItem("p0.auditOpen"); return v === null ? true : v === "1";
  });
  useEffect(() => { localStorage.setItem("p0.stackOpen", stackOpen ? "1" : "0"); }, [stackOpen]);
  useEffect(() => { localStorage.setItem("p0.auditOpen", auditOpen ? "1" : "0"); }, [auditOpen]);

  // Sync mode from server on load.
  useEffect(() => {
    fetch(API_BASE + "/v1/mode")
      .then(r => r.json())
      .then(data => { if (data.mode) setMode(data.mode); })
      .catch(() => {});
  }, []);

  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    fetch(API_BASE + "/v1/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: newMode }),
    }).catch(() => {});
  }, []);

  const handleSubmit = useCallback(async (text) => {
    const now = new Date().toTimeString().slice(0,8);
    const opTurn = { id: "op-" + Date.now(), role: "operator", t: now, text };
    setTurns(cur => [...cur, opTurn]);
    setStreaming("connecting · ariel is thinking");

    const tools = [];
    let responseText = "";
    let artifact = null;
    let errorText = null;

    try {
      const resp = await fetch(API_BASE + "/v1/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      let ended = false;

      outer: while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          let payload;
          try { payload = JSON.parse(line.slice(6)); } catch { continue; }

          if (payload.type === "tool_call") {
            tools.push({ name: payload.name, path: payload.path, ms: null, bytes: null });
            setStreaming(`calling ${payload.name} · ${tools.length} tool${tools.length !== 1 ? "s" : ""}`);
          } else if (payload.type === "tool_result") {
            // Update the most recent matching pending tool call.
            const idx = tools.findLastIndex(t => t.name === payload.name && t.ms === null);
            if (idx >= 0) tools[idx] = { ...tools[idx], ms: payload.ms, bytes: payload.bytes };
          } else if (payload.type === "token") {
            responseText = payload.text;
          } else if (payload.type === "artifact") {
            artifact = payload.artifact;
          } else if (payload.type === "error") {
            errorText = payload.text;
          } else if (payload.type === "end") {
            ended = true;
            break outer;
          }
        }
      }
    } catch (err) {
      errorText = String(err);
    }

    const turnId = "ai-" + Date.now();
    const nowEnd = new Date().toTimeString().slice(0,8);
    setTurns(cur => [...cur, {
      id: turnId,
      role: "ariel",
      t: nowEnd,
      streaming: true,
      tools,
      text: errorText ? `[error] ${errorText}` : responseText,
      ...(artifact && { artifact }),
    }]);
    setStreaming(null);

    // Flip streaming off after the component's animation should be done.
    const animMs = tools.length * 900 + (responseText.length * 35) + 1500;
    setTimeout(() => {
      setTurns(cur => cur.map(t => t.id === turnId ? { ...t, streaming: false } : t));
    }, animMs);

    // Refresh audit pane from server.
    fetch(API_BASE + "/v1/audit")
      .then(r => r.json())
      .then(data => setAudit(normalizeAuditEntries(data.entries).reverse()))
      .catch(() => {});
  }, []);

  return (
    <div className="app">
      <Header
        mode={mode}
        onModeChange={handleModeChange}
        layers={window.P0.LAYERS}
        session={window.P0.SESSION_STATS}
      />
      <div
        className="workspace"
        data-stack={stackOpen ? "open" : "closed"}
        data-audit={auditOpen ? "open" : "closed"}
      >
        <ChatPane
          turns={turns}
          onSubmit={handleSubmit}
          streaming={streaming}
          mode={mode}
        />
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
      <Footer session={window.P0.SESSION_STATS} mode={mode} />
      <TweaksPanel tweaks={tweaks} />
      <style>{HEADER_CSS + STACK_CSS + CHAT_CSS + AUDIT_CSS + FOOTER_CSS}</style>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
