/* global React, StatusDot, Chip, Kbd, cx, useTypewriter */
// Chat pane: operator ↔ Ariel von Prosper0.
// Streams responses with inline tool-call rendering.

const { useState, useRef, useEffect, useMemo } = React;

function ChatPane({ turns, onSubmit, streaming, mode }) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);
  const textaRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [turns, streaming]);

  const handleSend = () => {
    const v = draft.trim();
    if (!v || streaming) return;
    onSubmit(v);
    setDraft("");
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="pane chat-pane">
      <div className="pane-head">
        <div className="left">
          <span>terminal · operator ↔ ariel</span>
          <Chip tone="info" style={{ padding: "1px 6px" }}>
            <span className="mono">tty0</span>
          </Chip>
        </div>
        <div className="right mono xxs dim">
          session · {window.P0.SESSION_STATS.started}
        </div>
      </div>

      <div className="pane-body chat-body" ref={scrollRef}>
        <div className="chat-banner mono xs">
          <span className="quiet"># prosper0 orchestrator · qwen2.5:7b via ollama</span><br/>
          <span className="quiet"># vault: ~/prosper0 · mode: </span>
          <span className={"soft mode-text mode-" + mode}>{mode}</span>
          <span className="quiet"> · tools.config.yaml verified ed25519</span><br/>
          <span className="quiet"># type a message. shift+enter for newline.</span>
        </div>

        {turns.map(t => <Turn key={t.id} turn={t} />)}

        {streaming && <StreamingIndicator label={streaming} />}
      </div>

      <div className="chat-input">
        <div className="chat-input-gutter mono">
          <span className="dim">operator@prosper0</span>
          <span className="quiet">:~$</span>
        </div>
        <textarea
          ref={textaRef}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={handleKey}
          placeholder={streaming ? "ariel is working…" : "ask ariel something. ⏎ to send."}
          disabled={!!streaming}
          rows={2}
        />
        <div className="chat-input-foot">
          <div className="chat-hints mono xxs dim">
            <Kbd>↵</Kbd> send <span className="quiet">·</span>{" "}
            <Kbd>⇧↵</Kbd> newline <span className="quiet">·</span>{" "}
            <Kbd>⌘K</Kbd> clear
          </div>
          <button
            className={cx("chat-send mono", (!draft.trim() || streaming) && "disabled")}
            onClick={handleSend}
            disabled={!draft.trim() || !!streaming}
          >
            send <span className="quiet">›</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function Turn({ turn }) {
  if (turn.role === "operator") return <OperatorTurn turn={turn} />;
  return <ArielTurn turn={turn} />;
}

function OperatorTurn({ turn }) {
  return (
    <div className="turn turn-op">
      <div className="turn-head mono xxs">
        <span className="dim">[{turn.t}]</span>
        <span className="caps soft">operator</span>
        <span className="quiet">·</span>
        <span className="quiet">jared.allison</span>
      </div>
      <div className="turn-body op-text">
        <span className="quiet mono">&gt;</span> {turn.text}
      </div>
    </div>
  );
}

function ArielTurn({ turn }) {
  const [streamDone, setStreamDone] = useState(!turn.streaming);
  const [toolIdx, setToolIdx] = useState(turn.streaming ? -1 : (turn.tools?.length || 0));
  const [typed, setTyped] = useTypewriter(turn.text || "", !!turn.streaming);

  // If this turn is marked streaming, run tools sequentially then typewrite.
  useEffect(() => {
    if (!turn.streaming) return;
    let cancelled = false;
    const tools = turn.tools || [];
    let i = 0;
    const step = () => {
      if (cancelled) return;
      if (i < tools.length) {
        setToolIdx(i);
        i += 1;
        setTimeout(step, 520 + Math.random() * 400);
      } else {
        setToolIdx(tools.length);
        setTimeout(() => { if (!cancelled) setStreamDone(true); }, 180);
      }
    };
    step();
    return () => { cancelled = true; };
  }, [turn.id]);

  const shownText = turn.streaming ? typed : turn.text;

  return (
    <div className="turn turn-ai">
      <div className="turn-head mono xxs">
        <span className="dim">[{turn.t}]</span>
        <span className="caps ariel">ariel von prosper0</span>
        <span className="quiet">·</span>
        <span className="quiet">qwen2.5:7b</span>
      </div>

      {(turn.tools || []).length > 0 && (
        <ToolStream tools={turn.tools} upTo={turn.streaming ? toolIdx : turn.tools.length} />
      )}

      {shownText && (
        <div className="turn-body ai-text">
          {shownText}
          {turn.streaming && !streamDone && <span className="cursor-block" />}
        </div>
      )}

      {turn.artifact && (turn.streaming ? streamDone : true) && (
        <Artifact artifact={turn.artifact} />
      )}

      {turn.artifact?.kind === "draft" && (turn.streaming ? streamDone : true) && (
        <DraftActions />
      )}
    </div>
  );
}

function ToolStream({ tools, upTo }) {
  return (
    <div className="toolstream">
      {tools.map((tool, i) => {
        const state = i < upTo ? "done" : i === upTo ? "running" : "queued";
        return <ToolRow key={i} tool={tool} state={state} />;
      })}
    </div>
  );
}

function ToolRow({ tool, state }) {
  return (
    <div className={cx("tool-row", "state-" + state)}>
      <div className="tool-row-head mono xs">
        <span className={cx("tool-state-dot", "state-" + state)} />
        <span className="tool-verb">
          {state === "queued"  && "· queued"}
          {state === "running" && "› running"}
          {state === "done"    && "✓ done   "}
        </span>
        <span className="tool-name">{tool.name}</span>
        <span className="quiet">(</span>
        <span className="tool-path">{tool.path}</span>
        {tool.args && <span className="quiet"> {tool.args}</span>}
        <span className="quiet">)</span>
        {state === "done" && (
          <span className="tool-stats mono xxs quiet">
            · {tool.ms}ms{tool.bytes ? ` · ${(tool.bytes / 1024).toFixed(1)}kb` : ""}
          </span>
        )}
      </div>
      {state === "running" && (
        <div className="tool-progress">
          <div className="tool-progress-bar scan-bar" />
        </div>
      )}
    </div>
  );
}

function Artifact({ artifact }) {
  if (artifact.kind === "list") {
    return (
      <div className="artifact">
        <div className="artifact-head mono xxs caps dim">{artifact.title}</div>
        <ul className="artifact-list mono xs">
          {artifact.items.map((it, i) => {
            const [head, ...rest] = it.split(" — ");
            return (
              <li key={i}>
                <span className="accent">{head}</span>
                {rest.length > 0 && <span className="soft"> — {rest.join(" — ")}</span>}
              </li>
            );
          })}
        </ul>
      </div>
    );
  }
  if (artifact.kind === "draft") {
    return (
      <div className="artifact draft">
        <div className="artifact-head mono xxs caps dim">{artifact.title}</div>
        <div className="draft-meta mono xxs">
          {artifact.meta.map(([k, v]) => (
            <div key={k} className="draft-meta-row">
              <span className="dim">{k}</span>
              <span className="soft">{v}</span>
            </div>
          ))}
        </div>
        <div className="draft-body">
          {artifact.body.map((p, i) => <p key={i}>{p}</p>)}
        </div>
      </div>
    );
  }
  return null;
}

function DraftActions() {
  const [sent, setSent] = useState(false);
  if (sent) {
    return (
      <div className="draft-actions sent mono xs">
        <span className="accent">✓</span> transfer approved · audit entry written · employer CC'd
      </div>
    );
  }
  return (
    <div className="draft-actions">
      <div className="mono xxs quiet">operator gate · ai cannot send without you</div>
      <div className="draft-actions-buttons">
        <button className="btn-primary mono" onClick={() => setSent(true)}>
          approve & send <span className="quiet">(cc employer)</span>
        </button>
        <button className="btn-ghost mono">edit draft</button>
        <button className="btn-ghost mono">discard</button>
      </div>
    </div>
  );
}

function StreamingIndicator({ label }) {
  return (
    <div className="turn-head mono xxs" style={{ paddingLeft: 12, marginTop: 4 }}>
      <span className="cursor-block" style={{ width: "0.4em", height: "0.9em" }} />
      <span className="dim">{label}</span>
    </div>
  );
}

const CHAT_CSS = `
.chat-pane { background: var(--bg-0); }
.chat-body { padding: 12px 14px 18px; font-size: var(--fs-md); }
.chat-banner {
  border: 1px dashed var(--line);
  padding: 8px 10px;
  margin-bottom: 14px;
  line-height: 1.55;
}
.mode-text { font-weight: 600; }
.mode-text.mode-available  { color: var(--nominal); }
.mode-text.mode-in-meeting { color: var(--info); }
.mode-text.mode-deep-work  { color: var(--warn); }
.mode-text.mode-off-hours  { color: var(--fg-2); }

.turn { padding: 8px 0 14px; border-bottom: 1px dashed var(--line-soft); }
.turn:last-child { border-bottom: none; }
.turn-head { display: flex; align-items: center; gap: 6px; text-transform: lowercase; margin-bottom: 6px; }
.turn-head .caps { text-transform: uppercase; letter-spacing: 0.12em; }
.turn-head .ariel { color: var(--accent); }
.turn-body { line-height: 1.6; }
.op-text { color: var(--fg-1); font-family: var(--mono); font-size: var(--fs-sm); }
.op-text > span { margin-right: 4px; }
.ai-text { color: var(--fg-0); max-width: 70ch; }

/* Tool stream */
.toolstream {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-left: 2px solid color-mix(in oklch, var(--accent) 55%, var(--line-2));
  padding: 6px 10px;
  margin-bottom: 8px;
}
.tool-row { padding: 2px 0; }
.tool-row-head { display: flex; align-items: center; gap: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tool-state-dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.tool-state-dot.state-queued  { background: var(--fg-4); }
.tool-state-dot.state-running { background: var(--active); box-shadow: 0 0 0 3px color-mix(in oklch, var(--active) 25%, transparent); animation: pulse 1s infinite; }
.tool-state-dot.state-done    { background: var(--nominal); }
@keyframes pulse { 50% { opacity: 0.5; } }

.tool-row.state-queued  .tool-verb { color: var(--fg-3); }
.tool-row.state-running .tool-verb { color: var(--active); }
.tool-row.state-done    .tool-verb { color: var(--nominal); }
.tool-name { color: var(--fg-0); font-weight: 600; }
.tool-path { color: var(--fg-1); }
.tool-stats { margin-left: 4px; }

.tool-progress {
  margin-left: 16px;
  margin-top: 2px;
  height: 2px;
  background: var(--bg-3);
  overflow: hidden;
}
.tool-progress-bar { height: 100%; width: 100%; background: color-mix(in oklch, var(--accent) 30%, var(--bg-3)); }

/* Artifact */
.artifact {
  margin-top: 8px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  padding: 10px 12px;
}
.artifact-head { margin-bottom: 6px; }
.artifact-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.artifact-list li::before { content: "› "; color: var(--fg-3); }
.artifact-list .accent { color: var(--accent); font-weight: 600; }

/* Draft */
.artifact.draft { border-left: 2px solid var(--warn); }
.draft-meta {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px 12px;
  padding: 6px 0 8px;
  border-bottom: 1px dashed var(--line-soft);
  margin-bottom: 8px;
}
.draft-meta-row { display: flex; flex-direction: column; }
.draft-meta-row .dim { text-transform: uppercase; letter-spacing: 0.08em; font-size: 9px; }
.draft-body p { margin: 0 0 8px; line-height: 1.6; color: var(--fg-0); font-size: var(--fs-md); }
.draft-body p:last-child { margin-bottom: 0; }

.draft-actions {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.draft-actions-buttons { display: flex; gap: 8px; }
.btn-primary {
  padding: 6px 12px;
  background: color-mix(in oklch, var(--accent) 22%, var(--bg-3));
  color: var(--fg-0);
  border: 1px solid color-mix(in oklch, var(--accent) 60%, var(--line-2));
  border-radius: 2px;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.btn-primary:hover { background: color-mix(in oklch, var(--accent) 35%, var(--bg-3)); }
.btn-ghost {
  padding: 6px 12px;
  background: var(--bg-3);
  color: var(--fg-1);
  border: 1px solid var(--line-2);
  border-radius: 2px;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.btn-ghost:hover { background: var(--bg-4); }
.draft-actions.sent { color: var(--nominal); padding: 6px 0; }
.draft-actions.sent .accent { margin-right: 6px; }

/* Input */
.chat-input {
  flex: 0 0 auto;
  border-top: 1px solid var(--line);
  background: var(--bg-1);
  display: grid;
  grid-template-columns: auto 1fr;
  column-gap: 8px;
  align-items: start;
  padding: 10px 12px 8px;
}
.chat-input-gutter {
  display: flex; flex-direction: column; align-items: flex-end;
  gap: 2px;
  font-size: var(--fs-xs);
  padding-top: 6px;
}
.chat-input textarea {
  grid-column: 2;
  width: 100%;
  resize: vertical;
  min-height: 38px;
  max-height: 140px;
  padding: 6px 8px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  border-radius: 2px;
  font-family: var(--mono);
  font-size: var(--fs-sm);
  color: var(--fg-0);
}
.chat-input textarea:focus { border-color: color-mix(in oklch, var(--accent) 55%, var(--line-2)); }
.chat-input textarea::placeholder { color: var(--fg-3); }
.chat-input textarea:disabled { opacity: 0.6; cursor: not-allowed; }
.chat-input-foot {
  grid-column: 2;
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 6px;
}
.chat-hints { letter-spacing: 0.02em; }
.chat-send {
  padding: 5px 12px;
  background: color-mix(in oklch, var(--accent) 20%, var(--bg-3));
  color: var(--fg-0);
  border: 1px solid color-mix(in oklch, var(--accent) 60%, var(--line-2));
  border-radius: 2px;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.chat-send:hover { background: color-mix(in oklch, var(--accent) 35%, var(--bg-3)); }
.chat-send.disabled { opacity: 0.4; cursor: not-allowed; }

.accent { color: var(--accent); }
`;

Object.assign(window, { ChatPane, CHAT_CSS });
