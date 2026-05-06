/* global React, StatusDot, Chip, Kbd, cx */
// Top bar: identity, mode chip, stack health summary, shortcuts.

const { useState } = React;

function Header({ mode, onModeChange, layers, session }) {
  const [open, setOpen] = useState(false);
  const nominal = layers.filter(l => l.status === "nominal").length;
  const pending = layers.filter(l => l.status === "pending").length;
  const fault   = layers.filter(l => l.status === "fault").length;

  return (
    <header className="hdr">
      <div className="hdr-left">
        <div className="brandmark" aria-label="prosper0">
          <span className="brandmark-glyph mono">P0</span>
          <div className="brandmark-text">
            <div className="mono caps xxs dim">local-mind-foundation · work instance</div>
            <div className="brandmark-name mono">prosper0<span className="quiet">/operator-console</span></div>
          </div>
        </div>
      </div>

      <div className="hdr-center">
        <HealthSummary nominal={nominal} pending={pending} fault={fault} total={layers.length} />
      </div>

      <div className="hdr-right">
        <div className="hdr-item" title="Active instance AI">
          <span className="mono caps xxs dim">ai</span>
          <span className="mono sm">ariel von prosper0</span>
          <span className="dim mono xxs">· qwen2.5:7b</span>
        </div>

        <div className="hdr-sep" />

        <ModeChip mode={mode} onChange={onModeChange} open={open} setOpen={setOpen} />

        <div className="hdr-sep" />

        <div className="hdr-item" title="Operator · hardware-paired">
          <span className="mono caps xxs dim">operator</span>
          <span className="mono sm">jared.allison</span>
          <span className="chip ok" style={{ padding: "1px 6px" }}>
            <StatusDot status="nominal" /> paired
          </span>
        </div>
      </div>
    </header>
  );
}

function HealthSummary({ nominal, pending, fault, total }) {
  return (
    <div className="health">
      <div className="mono caps xxs dim">stack</div>
      <div className="health-counts mono">
        <span className="health-count ok"><StatusDot status="nominal" /> {nominal} nominal</span>
        <span className="health-sep">·</span>
        <span className="health-count pending"><StatusDot status="pending" /> {pending} pending</span>
        {fault > 0 && <>
          <span className="health-sep">·</span>
          <span className="health-count fault"><StatusDot status="fault" /> {fault} fault</span>
        </>}
      </div>
      <div className="health-bars" aria-hidden="true">
        {Array.from({ length: total }).map((_, i) => {
          const tone = i < nominal ? "ok" : i < nominal + pending ? "pending" : "fault";
          return <span key={i} className={"health-bar " + tone} />;
        })}
      </div>
    </div>
  );
}

function ModeChip({ mode, onChange, open, setOpen }) {
  const modes = window.P0.MODES;
  const current = modes.find(m => m.id === mode) || modes[0];
  return (
    <div className="mode-wrap">
      <button
        className={cx("mode-chip mono", "mode-" + mode)}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="mode-label caps xxs dim">mode</span>
        <span className="mode-value">{current.label}</span>
        <span className="mode-caret">▾</span>
      </button>
      {open && (
        <div className="mode-menu" onMouseLeave={() => setOpen(false)}>
          {modes.map(m => (
            <button
              key={m.id}
              className={cx("mode-opt", m.id === mode && "on")}
              onClick={() => { onChange(m.id); setOpen(false); }}
            >
              <div className="mode-opt-head mono">
                <span className={"dot mode-" + m.id} />
                <span className="mode-opt-name">{m.label}</span>
                {m.id === mode && <span className="mono xxs dim">· current</span>}
              </div>
              <div className="mode-opt-hint xs quiet mono">{m.hint}</div>
            </button>
          ))}
          <div className="mode-menu-foot xs quiet mono">mode is persisted to vault/modes.state</div>
        </div>
      )}
    </div>
  );
}

/* Inline style block for header — kept local so it doesn't collide. */
const HEADER_CSS = `
.hdr {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: center;
  padding: 10px 16px;
  background: linear-gradient(to bottom, var(--bg-2), var(--bg-1));
  border-bottom: 1px solid var(--line);
  height: 54px;
  flex: 0 0 auto;
}
.hdr-left, .hdr-right { display: flex; align-items: center; gap: 14px; }
.hdr-right { justify-content: flex-end; }
.hdr-center { display: flex; justify-content: center; }

.brandmark { display: flex; align-items: center; gap: 10px; }
.brandmark-glyph {
  width: 34px; height: 34px;
  display: grid; place-items: center;
  background: color-mix(in oklch, var(--accent) 18%, var(--bg-3));
  color: var(--accent);
  font-size: 12px; font-weight: 700;
  border: 1px solid color-mix(in oklch, var(--accent) 45%, var(--line-2));
  border-radius: 3px;
  letter-spacing: 0.05em;
}
.brandmark-name { font-size: 13px; font-weight: 600; letter-spacing: 0.02em; }

.hdr-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.hdr-sep {
  width: 1px; height: 22px; background: var(--line);
}

/* Health strip */
.health {
  display: flex; align-items: center; gap: 14px;
  padding: 6px 14px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: 3px;
}
.health-counts { display: flex; gap: 8px; font-size: 11px; align-items: center; }
.health-count { display: inline-flex; gap: 6px; align-items: center; }
.health-count.ok      { color: var(--nominal); }
.health-count.pending { color: var(--fg-2); }
.health-count.fault   { color: var(--fault); }
.health-sep { color: var(--fg-4); }
.health-bars { display: flex; gap: 3px; }
.health-bar {
  width: 16px; height: 8px; display: inline-block;
  background: var(--bg-3);
  border: 1px solid var(--line);
}
.health-bar.ok      { background: color-mix(in oklch, var(--nominal) 55%, var(--bg-3)); border-color: color-mix(in oklch, var(--nominal) 40%, var(--line-2)); }
.health-bar.pending { background: var(--bg-3); }
.health-bar.fault   { background: color-mix(in oklch, var(--fault) 55%, var(--bg-3)); }

/* Mode chip */
.mode-wrap { position: relative; }
.mode-chip {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 10px;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-radius: 3px;
  font-size: 11px;
  letter-spacing: 0.06em;
}
.mode-chip .mode-label { text-transform: uppercase; }
.mode-chip .mode-value { font-weight: 600; color: var(--fg-0); }
.mode-chip .mode-caret { color: var(--fg-3); font-size: 10px; }
.mode-chip.mode-available  { border-color: color-mix(in oklch, var(--nominal) 50%, var(--line-2)); }
.mode-chip.mode-available  .mode-value { color: var(--nominal); }
.mode-chip.mode-in-meeting { border-color: color-mix(in oklch, var(--info) 50%, var(--line-2)); }
.mode-chip.mode-in-meeting .mode-value { color: var(--info); }
.mode-chip.mode-deep-work  { border-color: color-mix(in oklch, var(--warn) 50%, var(--line-2)); }
.mode-chip.mode-deep-work  .mode-value { color: var(--warn); }
.mode-chip.mode-off-hours  { border-color: var(--line-2); }
.mode-chip.mode-off-hours  .mode-value { color: var(--fg-2); }

.mode-menu {
  position: absolute; right: 0; top: calc(100% + 6px);
  width: 280px;
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  box-shadow: 0 12px 28px rgba(0,0,0,0.45);
  border-radius: 3px;
  z-index: 20;
  padding: 4px;
}
.mode-opt {
  display: block; width: 100%; text-align: left;
  padding: 8px 10px;
  background: transparent;
  border-radius: 2px;
}
.mode-opt:hover { background: var(--bg-3); }
.mode-opt.on { background: color-mix(in oklch, var(--accent) 15%, var(--bg-3)); }
.mode-opt-head { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.mode-opt-hint { margin-top: 3px; }
.mode-menu-foot { padding: 6px 10px; border-top: 1px solid var(--line-soft); }

.dot.mode-available  { color: var(--nominal); }
.dot.mode-in-meeting { color: var(--info); }
.dot.mode-deep-work  { color: var(--warn); }
.dot.mode-off-hours  { color: var(--fg-3); box-shadow: none; }
`;

Object.assign(window, { Header, HEADER_CSS });
