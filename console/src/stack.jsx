/* global React, StatusDot, Chip, cx */
// The six-layer stack diagram — center column.
// Shows each layer as a horizontal bar, with live metrics.
// Click a layer to pin it and show its detail (files, tool surface, events).

const { useState, useMemo } = React;

function StackPane({ layers, focusedId, setFocusedId, tools, audit, onCollapse }) {
  const focused = layers.find(l => l.id === focusedId) || layers[layers.length - 1];

  return (
    <div className="pane stack-pane">
      <div className="pane-head">
        <div className="left">
          <span>stack · six layers</span>
          <Chip tone="">
            <span className="mono">{layers.filter(l => l.status === "nominal").length}</span>
            <span className="dim">/ {layers.length} online</span>
          </Chip>
        </div>
        <div className="right mono xxs dim">
          <span>click a layer · drill in</span>
          {onCollapse && (
            <button className="pane-collapse" onClick={onCollapse} title="minimize stack">×</button>
          )}
        </div>
      </div>

      <div className="pane-body stack-body">
        <div className="stack-ladder">
          {/* vertical guide */}
          <div className="stack-rail" aria-hidden="true">
            <div className="stack-rail-line" />
            {layers.map(l => (
              <div key={l.id} className="stack-rail-tick">
                <span className="mono xxs dim">{l.code}</span>
              </div>
            ))}
          </div>

          <div className="stack-rows">
            {layers.map(l => (
              <LayerRow
                key={l.id}
                layer={l}
                focused={l.id === focused.id}
                onClick={() => setFocusedId(l.id)}
              />
            ))}
          </div>
        </div>

        <div className="rule" style={{ margin: "18px 14px 10px" }}>
          <span>layer detail · {focused.code} {focused.name.toLowerCase()}</span>
        </div>

        <LayerDetail layer={focused} tools={tools} audit={audit} />
      </div>
    </div>
  );
}

function LayerRow({ layer, focused, onClick }) {
  const tone = {
    nominal: "ok",
    active:  "active",
    warn:    "warn",
    fault:   "fault",
    pending: "",
  }[layer.status] || "";

  return (
    <button className={cx("layer-row", focused && "focused", "tone-" + (tone || "dim"))} onClick={onClick}>
      <div className="layer-row-head">
        <div className="layer-row-code mono">
          <span className="xxs dim">layer</span>
          <span className="layer-num">{layer.id}</span>
        </div>
        <div className="layer-row-title">
          <div className="layer-row-name">{layer.name}</div>
          <div className="layer-row-summary mono xxs quiet">{layer.summary}</div>
        </div>
        <div className="layer-row-status">
          <Chip tone={tone}>
            <StatusDot status={layer.status} />
            {layer.status}
          </Chip>
        </div>
      </div>

      <div className="layer-row-metrics mono xs">
        {layer.metrics.map(([k, v]) => (
          <div key={k} className="lrm">
            <span className="lrm-k dim">{k}</span>
            <span className="lrm-v">{v}</span>
          </div>
        ))}
      </div>
    </button>
  );
}

function LayerDetail({ layer, tools, audit }) {
  const layerTools = tools.filter(t => t.layer === layer.id);
  const layerAudit = audit.filter(a => a.layer === layer.id).slice(0, 5);

  return (
    <div className="layer-detail">
      <div className="ld-col">
        <div className="ld-title mono caps xxs dim">files in repo</div>
        <ul className="ld-files mono xs">
          {layer.files.map(f => (
            <li key={f}>
              <span className="quiet">$</span> cat <span className="soft">{f}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="ld-col">
        <div className="ld-title mono caps xxs dim">tool surface · {layerTools.length}</div>
        {layerTools.length === 0 ? (
          <div className="mono xs quiet">— no tools exposed by this layer</div>
        ) : (
          <ul className="ld-tools">
            {layerTools.map(t => (
              <li key={t.id} className={cx("ld-tool", !t.allow && "denied")}>
                <span className="ld-tool-name mono xs">{t.id}</span>
                <Chip tone={t.allow ? "ok" : "fault"} style={{ padding: "1px 6px" }}>
                  {t.allow ? "allow" : "deny"}
                </Chip>
                <span className="ld-tool-note mono xxs quiet">{t.note}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="ld-col">
        <div className="ld-title mono caps xxs dim">recent events · {layerAudit.length}</div>
        {layerAudit.length === 0 ? (
          <div className="mono xs quiet">— nothing recorded for this layer yet</div>
        ) : (
          <ul className="ld-events mono xs">
            {layerAudit.map(a => (
              <li key={a.id}>
                <span className="quiet">{a.t}</span>{" "}
                <span className={cx("ld-ev-kind", "kind-" + a.kind)}>{a.kind}</span>{" "}
                <span className="soft">{a.verb}</span>{" "}
                <span className="dim">→ {a.target}</span>
                {a.note && <span className="quiet"> · {a.note}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

const STACK_CSS = `
.stack-pane { background: var(--bg-1); }
.stack-body { padding: 12px 14px 18px; }

/* Vertical ladder */
.stack-ladder {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 8px;
  position: relative;
}
.stack-rail {
  position: relative;
  display: flex; flex-direction: column;
  justify-content: space-between;
  padding: 18px 0;
}
.stack-rail-line {
  position: absolute;
  top: 12px; bottom: 12px;
  left: 50%;
  width: 1px;
  background: repeating-linear-gradient(to bottom, var(--line-2) 0 4px, transparent 4px 8px);
}
.stack-rail-tick {
  position: relative;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-1);
  padding: 2px 0;
  z-index: 1;
}

.stack-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.layer-row {
  text-align: left;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-left: 3px solid var(--line);
  border-radius: 2px;
  padding: 10px 12px;
  display: flex; flex-direction: column; gap: 8px;
  transition: background 0.1s, border-color 0.15s;
}
.layer-row:hover { background: var(--bg-3); }
.layer-row.focused {
  background: color-mix(in oklch, var(--accent) 8%, var(--bg-3));
  border-color: color-mix(in oklch, var(--accent) 55%, var(--line-2));
}
.layer-row.tone-ok      { border-left-color: var(--nominal); }
.layer-row.tone-warn    { border-left-color: var(--warn); }
.layer-row.tone-fault   { border-left-color: var(--fault); }
.layer-row.tone-active  { border-left-color: var(--active); }
.layer-row.tone-dim     { border-left-color: var(--line-2); }

.layer-row-head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
}
.layer-row-code {
  display: flex; flex-direction: column; align-items: center;
  min-width: 40px;
}
.layer-row-code .layer-num {
  font-size: 20px; font-weight: 700; line-height: 1; color: var(--fg-1);
}
.layer-row-name { font-size: 13px; font-weight: 600; letter-spacing: 0.01em; }
.layer-row-summary { margin-top: 2px; }

.layer-row-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 4px 14px;
  padding-left: 52px;
}
.lrm { display: flex; justify-content: space-between; gap: 8px; border-bottom: 1px dashed var(--line-soft); padding: 3px 0; }
.lrm-k { text-transform: uppercase; letter-spacing: 0.08em; font-size: 10px; }
.lrm-v { color: var(--fg-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Layer detail */
.layer-detail {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 1.4fr;
  gap: 18px;
  padding: 4px 14px 10px;
}
.ld-col { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.ld-title { margin-bottom: 2px; }
.ld-files, .ld-tools, .ld-events {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 3px;
}
.ld-files li { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.ld-tool {
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: 8px; align-items: center;
}
.ld-tool-name { color: var(--fg-0); }
.ld-tool.denied .ld-tool-name { color: var(--fg-2); text-decoration: line-through; text-decoration-color: var(--fault); }

.ld-events li {
  padding: 2px 0;
  border-bottom: 1px dashed var(--line-soft);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ld-ev-kind {
  text-transform: uppercase; letter-spacing: 0.08em;
  font-size: 9px;
  padding: 1px 5px;
  border: 1px solid var(--line-2);
  border-radius: 2px;
  color: var(--fg-2);
}
.ld-ev-kind.kind-tool   { color: var(--info);    border-color: color-mix(in oklch, var(--info) 40%, var(--line-2)); }
.ld-ev-kind.kind-verify { color: var(--nominal); border-color: color-mix(in oklch, var(--nominal) 40%, var(--line-2)); }
.ld-ev-kind.kind-deny   { color: var(--fault);   border-color: color-mix(in oklch, var(--fault) 50%, var(--line-2)); }
.ld-ev-kind.kind-model  { color: var(--accent);  border-color: color-mix(in oklch, var(--accent) 40%, var(--line-2)); }
.ld-ev-kind.kind-boot   { color: var(--warn);    border-color: color-mix(in oklch, var(--warn) 40%, var(--line-2)); }
`;

Object.assign(window, { StackPane, STACK_CSS });
