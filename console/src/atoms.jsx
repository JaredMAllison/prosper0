/* global React */
// Small shared primitives.

const { useEffect, useRef, useState } = React;

function cx(...parts) { return parts.filter(Boolean).join(" "); }

function StatusDot({ status = "nominal" }) {
  const color = {
    nominal: "var(--nominal)",
    active:  "var(--active)",
    warn:    "var(--warn)",
    fault:   "var(--fault)",
    info:    "var(--info)",
    pending: "var(--fg-3)",
  }[status] || "var(--fg-3)";
  return (
    <span
      className="dot"
      style={{
        color,
        boxShadow: status === "pending"
          ? "none"
          : `0 0 0 2px color-mix(in oklch, ${color} 25%, transparent)`,
        opacity: status === "pending" ? 0.6 : 1,
      }}
    />
  );
}

function Chip({ tone = "", children, style, title, onClick }) {
  return (
    <span className={cx("chip", tone)} style={style} title={title} onClick={onClick}>
      {children}
    </span>
  );
}

function Kbd({ children }) { return <span className="kbd">{children}</span>; }

function Rule({ children }) { return <div className="rule">{children}</div>; }

/* Tiny hook: blink a value briefly on change (for live counters) */
function usePulseKey(value) {
  const [k, setK] = useState(0);
  const first = useRef(true);
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    setK(v => v + 1);
  }, [value]);
  return k;
}

/* Typewriter: reveal text char-by-char. done() fires when complete. */
function useTypewriter(fullText, enabled, speed = 14) {
  const [shown, setShown] = useState("");
  const doneRef = useRef(null);

  useEffect(() => {
    if (!enabled) { setShown(fullText); return; }
    setShown("");
    let i = 0;
    const id = setInterval(() => {
      i += Math.max(1, Math.floor(Math.random() * 4));
      if (i >= fullText.length) {
        setShown(fullText);
        clearInterval(id);
        if (doneRef.current) doneRef.current();
      } else {
        setShown(fullText.slice(0, i));
      }
    }, speed);
    return () => clearInterval(id);
  }, [fullText, enabled, speed]);

  return [shown, (cb) => { doneRef.current = cb; }];
}

/* Nicer tiny count-up */
function Count({ value, suffix = "" }) {
  return <span className="mono">{value.toLocaleString()}{suffix}</span>;
}

Object.assign(window, { cx, StatusDot, Chip, Kbd, Rule, usePulseKey, useTypewriter, Count });
