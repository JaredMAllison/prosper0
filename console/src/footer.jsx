/* global React, Count, cx */
// Bottom status bar: tokens, context, enforcement stats, clock.

const { useState, useEffect } = React;

function Footer({ session, mode }) {
  const [clock, setClock] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const ctxPct = (session.context.used / session.context.max) * 100;
  const hhmmss = clock.toTimeString().slice(0, 8);

  return (
    <footer className="ftr mono xxs">
      <div className="ftr-left">
        <FtrCell label="orchestrator" value="up" tone="ok" />
        <FtrCell label="inference" value="ollama ·  warm" tone="ok" />
        <FtrCell label="config sig" value="verified" tone="ok" />
        <FtrCell label="vault iso" value="verified" tone="ok" />
      </div>
      <div className="ftr-center">
        <FtrCell label="tools ok" value={session.tools.ok} />
        <FtrCell label="denied"   value={session.tools.denied} tone={session.tools.denied > 0 ? "warn" : ""} />
        <FtrCell label="transfers" value={`${session.transfers.sent}/${session.transfers.drafted}`} />
        <FtrCell label="tokens" value={<><Count value={session.tokens.in} />↓ <Count value={session.tokens.out} />↑</>} />
        <FtrCell label="context" value={
          <span className="ftr-ctx">
            <span className="ftr-ctx-bar">
              <span className="ftr-ctx-fill" style={{ width: ctxPct + "%" }} />
            </span>
            <span><Count value={session.context.used} /> / <Count value={session.context.max} /></span>
          </span>
        } />
      </div>
      <div className="ftr-right">
        <span className="dim">mode</span>
        <span className={"soft mode-text mode-" + mode}>{mode}</span>
        <span className="sep">·</span>
        <span className="dim">local</span>
        <span className="soft">{hhmmss}</span>
      </div>
    </footer>
  );
}

function FtrCell({ label, value, tone }) {
  return (
    <div className={cx("ftr-cell", tone && ("tone-" + tone))}>
      <span className="dim">{label}</span>
      <span className="val">{value}</span>
    </div>
  );
}

const FOOTER_CSS = `
.ftr {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: center;
  padding: 5px 14px;
  background: var(--bg-2);
  border-top: 1px solid var(--line);
  height: 28px;
  flex: 0 0 auto;
  letter-spacing: 0.04em;
}
.ftr-left, .ftr-center, .ftr-right { display: flex; align-items: center; gap: 12px; }
.ftr-right { justify-content: flex-end; gap: 6px; }
.ftr-cell { display: flex; align-items: baseline; gap: 6px; }
.ftr-cell .dim { text-transform: uppercase; letter-spacing: 0.08em; font-size: 9px; }
.ftr-cell .val { color: var(--fg-0); font-size: 10px; }
.ftr-cell.tone-ok .val    { color: var(--nominal); }
.ftr-cell.tone-warn .val  { color: var(--warn); }
.ftr-cell.tone-fault .val { color: var(--fault); }
.ftr-ctx { display: inline-flex; align-items: center; gap: 6px; }
.ftr-ctx-bar {
  width: 60px; height: 5px; background: var(--bg-3); border: 1px solid var(--line); display: inline-block;
}
.ftr-ctx-fill { display: block; height: 100%; background: color-mix(in oklch, var(--accent) 60%, var(--bg-3)); }
.ftr .sep { color: var(--fg-4); margin: 0 2px; }
`;

Object.assign(window, { Footer, FOOTER_CSS });
