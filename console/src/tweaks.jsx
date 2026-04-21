/* global React, cx */
// Tweaks panel — variations exposed via the toolbar toggle.

const { useEffect, useState, useRef } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accentHue": 185,
  "density": "comfortable",
  "auditVerbosity": "normal",
  "toolGating": "streamed"
}/*EDITMODE-END*/;

const HUES = [
  { v: 185, label: "teal"   },
  { v: 155, label: "green"  },
  { v: 95,  label: "amber"  },
  { v: 55,  label: "orange" },
  { v: 300, label: "magenta"},
  { v: 240, label: "blue"   },
];

function useTweaks() {
  const [values, setValues] = useState(TWEAK_DEFAULTS);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onMsg = (ev) => {
      const d = ev.data;
      if (!d || typeof d !== "object") return;
      if (d.type === "__activate_edit_mode")   setVisible(true);
      if (d.type === "__deactivate_edit_mode") setVisible(false);
    };
    window.addEventListener("message", onMsg);
    window.parent.postMessage({ type: "__edit_mode_available" }, "*");
    return () => window.removeEventListener("message", onMsg);
  }, []);

  // Apply accent hue as CSS var
  useEffect(() => {
    document.documentElement.style.setProperty(
      "--accent",
      `oklch(0.80 0.10 ${values.accentHue})`
    );
    document.documentElement.style.setProperty(
      "--nominal",
      `oklch(0.78 0.10 ${values.accentHue})`
    );
    document.documentElement.setAttribute("data-density", values.density === "comfortable" ? "" : values.density);
  }, [values.accentHue, values.density]);

  const update = (k, v) => {
    setValues(cur => {
      const next = { ...cur, [k]: v };
      window.parent.postMessage({ type: "__edit_mode_set_keys", edits: { [k]: v } }, "*");
      return next;
    });
  };

  return { values, visible, update };
}

function TweaksPanel({ tweaks }) {
  if (!tweaks.visible) return null;
  const { values, update } = tweaks;
  return (
    <div className="tweaks">
      <h4>
        <span>tweaks</span>
        <span className="xxs quiet">prosper0</span>
      </h4>

      <div className="row">
        <div className="row-label">accent hue</div>
        <div className="hue-swatches">
          {HUES.map(h => (
            <button
              key={h.v}
              className={cx(values.accentHue === h.v && "on")}
              style={{ background: `oklch(0.75 0.10 ${h.v})` }}
              title={h.label}
              onClick={() => update("accentHue", h.v)}
            />
          ))}
        </div>
      </div>

      <div className="row">
        <div className="row-label">density</div>
        <div className="seg">
          {["comfortable", "dense", "ultra"].map(d => (
            <button key={d} className={cx(values.density === d && "on")}
                    onClick={() => update("density", d)}>
              {d.slice(0, 5)}
            </button>
          ))}
        </div>
      </div>

      <div className="row">
        <div className="row-label">audit verbosity</div>
        <div className="seg">
          {["compact", "normal"].map(v => (
            <button key={v} className={cx(values.auditVerbosity === v && "on")}
                    onClick={() => update("auditVerbosity", v)}>
              {v}
            </button>
          ))}
        </div>
      </div>

      <div className="row">
        <div className="row-label">tool gating</div>
        <div className="seg">
          {["streamed", "silent", "gated"].map(g => (
            <button key={g} className={cx(values.toolGating === g && "on")}
                    onClick={() => update("toolGating", g)}>
              {g}
            </button>
          ))}
        </div>
      </div>

      <div className="row">
        <div className="row-label quiet">
          toolbar · toggle Tweaks to hide
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { useTweaks, TweaksPanel });
