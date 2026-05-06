/* global React, StatusDot, Chip, cx */
// Audit stream pane — live transparency feed. Right column.

const { useMemo, useState } = React;

function AuditPane({ events, verbosity = "normal", onCollapse }) {
  const [filter, setFilter] = useState("all");

  const shown = useMemo(() => {
    let e = events;
    if (filter === "tool")    e = e.filter(x => x.kind === "tool");
    if (filter === "verify")  e = e.filter(x => x.kind === "verify");
    if (filter === "deny")    e = e.filter(x => x.kind === "deny");
    if (verbosity === "compact") return e.slice(0, 14);
    return e;
  }, [events, filter, verbosity]);

  const counts = useMemo(() => ({
    total:  events.length,
    tool:   events.filter(e => e.kind === "tool").length,
    verify: events.filter(e => e.kind === "verify").length,
    deny:   events.filter(e => e.kind === "deny").length,
  }), [events]);

  return (
    <div className="pane audit-pane">
      <div className="pane-head">
        <div className="left">
          <span>audit · transparency</span>
          <Chip tone="ok" style={{ padding: "1px 6px" }}>
            <StatusDot status="nominal" /> tamper-evident
          </Chip>
        </div>
        <div className="right">
          <span className="mono xxs dim">ed25519 hash chain</span>
          {onCollapse && (
            <button className="pane-collapse" onClick={onCollapse} title="minimize transparency">×</button>
          )}
        </div>
      </div>

      <div className="audit-filters">
        <FilterBtn id="all"    active={filter === "all"}    onClick={setFilter}>all · {counts.total}</FilterBtn>
        <FilterBtn id="tool"   active={filter === "tool"}   onClick={setFilter}>tool · {counts.tool}</FilterBtn>
        <FilterBtn id="verify" active={filter === "verify"} onClick={setFilter}>verify · {counts.verify}</FilterBtn>
        <FilterBtn id="deny"   active={filter === "deny"}   onClick={setFilter}>deny · {counts.deny}</FilterBtn>
      </div>

      <div className="pane-body audit-body mono">
        <div className="audit-legend xs quiet">
          <span>timestamp</span>
          <span>layer</span>
          <span>kind</span>
          <span>event</span>
          <span>dur</span>
        </div>

        <ul className="audit-list">
          {shown.map(e => <AuditRow key={e.id} e={e} />)}
        </ul>

        <div className="audit-foot mono xxs quiet">
          <div>chain head · <span className="soft">sha256:7a4e…2f3b</span></div>
          <div>rotated · 2026-04-21 00:00:00z</div>
          <div>destination · transparency/audit.log.jsonl (append-only)</div>
        </div>
      </div>

      <div className="audit-transfers">
        <div className="rule" style={{ margin: "0 12px 8px" }}><span>data transfers · operator-gated</span></div>
        <TransferRow
          n="—"
          direction="pending"
          label="Draft · status note to manager"
          meta="cc: transparency@employer"
          state="awaiting-operator"
        />
        <div className="audit-transfers-empty mono xxs quiet">
          no completed transfers this session · bridge idle
        </div>
      </div>
    </div>
  );
}

function FilterBtn({ id, active, onClick, children }) {
  return (
    <button
      className={cx("audit-filter mono", active && "on")}
      onClick={() => onClick(id)}
    >
      {children}
    </button>
  );
}

function AuditRow({ e }) {
  const ok = e.ok !== false;
  return (
    <li className={cx("audit-row", "kind-" + e.kind, !ok && "failed")}>
      <div className="ar-main">
        <span className="ar-t quiet">{e.t}</span>
        <span className="ar-layer">L{e.layer}</span>
        <span className={cx("ar-kind", "kind-" + e.kind)}>{e.kind}</span>
        <span className="ar-verb">{e.verb}</span>
        <span className="ar-arrow quiet">→</span>
        <span className="ar-target">{e.target}</span>
        <span className="ar-dur quiet">{e.dur ? `${e.dur}ms` : "—"}</span>
      </div>
      {e.note && <div className="ar-note quiet xxs">{e.note}</div>}
    </li>
  );
}

function TransferRow({ n, direction, label, meta, state }) {
  return (
    <div className={cx("xfer mono", "xfer-" + state)}>
      <div className="xfer-top">
        <span className="xfer-n xxs">{n}</span>
        <span className="xfer-dir xxs dim">{direction}</span>
        <span className="xfer-state xxs">{state}</span>
      </div>
      <div className="xfer-label">{label}</div>
      <div className="xfer-meta xxs quiet">{meta}</div>
    </div>
  );
}

const AUDIT_CSS = `
.audit-pane { background: var(--bg-1); }

.audit-filters {
  display: flex;
  gap: 0;
  padding: 6px 10px;
  border-bottom: 1px solid var(--line);
  background: var(--bg-1);
  flex: 0 0 auto;
}
.audit-filter {
  padding: 4px 10px;
  font-size: var(--fs-xxs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--fg-2);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 2px;
  margin-right: 2px;
}
.audit-filter:hover { color: var(--fg-0); background: var(--bg-3); }
.audit-filter.on {
  color: var(--fg-0);
  background: var(--bg-3);
  border-color: var(--line-2);
}

.audit-body { padding: 8px 10px 14px; font-size: var(--fs-xs); }
.audit-legend {
  display: grid;
  grid-template-columns: 84px 28px 50px 1fr 40px;
  gap: 6px;
  padding: 2px 4px 6px;
  border-bottom: 1px dashed var(--line-soft);
  text-transform: uppercase; letter-spacing: 0.1em; font-size: 9px;
}

.audit-list { list-style: none; padding: 0; margin: 0; }
.audit-row {
  padding: 4px 4px;
  border-bottom: 1px dashed var(--line-soft);
}
.audit-row:hover { background: var(--bg-2); }
.ar-main {
  display: grid;
  grid-template-columns: 84px 28px 50px 1fr 40px;
  gap: 6px;
  align-items: center;
  overflow: hidden;
}
.ar-main > * { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ar-t { font-size: 10px; }
.ar-layer { color: var(--fg-1); font-weight: 600; font-size: 10px; }
.ar-kind {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 1px 4px;
  border: 1px solid var(--line-2);
  border-radius: 2px;
  text-align: center;
  color: var(--fg-2);
  background: var(--bg-2);
}
.ar-kind.kind-tool   { color: var(--info);    border-color: color-mix(in oklch, var(--info) 40%, var(--line-2)); }
.ar-kind.kind-verify { color: var(--nominal); border-color: color-mix(in oklch, var(--nominal) 40%, var(--line-2)); }
.ar-kind.kind-deny   { color: var(--fault);   border-color: color-mix(in oklch, var(--fault) 50%, var(--line-2)); background: var(--fault-dim); }
.ar-kind.kind-model  { color: var(--accent);  border-color: color-mix(in oklch, var(--accent) 40%, var(--line-2)); }
.ar-kind.kind-boot   { color: var(--warn);    border-color: color-mix(in oklch, var(--warn) 40%, var(--line-2)); }
.ar-kind.kind-info   { color: var(--fg-2); }
.ar-verb { color: var(--fg-0); font-weight: 500; }
.ar-target { color: var(--fg-1); }
.ar-dur { text-align: right; font-size: 10px; }
.ar-note { padding-left: 120px; padding-top: 2px; }

.audit-row.failed .ar-target { color: var(--fault); }
.audit-row.failed { background: color-mix(in oklch, var(--fault) 6%, transparent); }

.audit-foot {
  margin-top: 10px;
  padding: 8px 4px 0;
  border-top: 1px solid var(--line);
  display: flex; flex-direction: column; gap: 2px;
}

/* Transfers */
.audit-transfers {
  flex: 0 0 auto;
  border-top: 1px solid var(--line);
  padding: 10px 0 12px;
  background: var(--bg-2);
}
.xfer {
  margin: 0 12px 6px;
  padding: 8px 10px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-left: 2px solid var(--warn);
  border-radius: 2px;
}
.xfer-top {
  display: flex; gap: 8px; align-items: center; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;
}
.xfer-n { color: var(--fg-3); }
.xfer-state { color: var(--warn); font-weight: 600; }
.xfer-label { font-size: var(--fs-sm); color: var(--fg-0); }
.xfer-meta { margin-top: 2px; }
.audit-transfers-empty { padding: 2px 14px 2px; }
`;

Object.assign(window, { AuditPane, AUDIT_CSS });
