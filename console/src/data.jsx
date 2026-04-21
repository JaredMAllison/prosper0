/* global React */
// Seed data: six layers, audit events, chat turns, vault files, tool config.
// Designed to read like a real snapshot of Prosper0 a few minutes into a workday.

const LAYERS = [
  {
    id: 6, code: "L6", name: "Portable Deployment",
    summary: "Encrypted USB · hardware-paired · single desktop shortcut",
    status: "pending",           // not started in real repo
    metrics: [
      ["drive",    "— not enrolled"],
      ["pairing",  "— no host fingerprint"],
      ["size",     "— n/a"],
    ],
    files: ["deploy/compose.yaml", "deploy/pull-model.sh", "deploy/drive-enroll.md"],
  },
  {
    id: 5, code: "L5", name: "Testing Infrastructure",
    summary: "Sample data · model-version diff · boundary assertions",
    status: "pending",
    metrics: [
      ["suite",     "boundary, bridge, model"],
      ["last run",  "— never"],
      ["fixtures",  "— not generated"],
    ],
    files: ["tests/boundary/", "tests/bridge/", "tests/model_diff/"],
  },
  {
    id: 4, code: "L4", name: "Employer Transparency",
    summary: "Ed25519-signed tool config · audit trail · transfer manifest",
    status: "nominal",
    metrics: [
      ["tests",      "33 / 33 passing"],
      ["config sig", "ed25519 · verified 00:00:14 ago"],
      ["audit lag",  "0 events queued"],
    ],
    files: [
      "transparency/tools.config.yaml",
      "transparency/audit.log.jsonl",
      "transparency/transfers.jsonl",
      "transparency/report.py",
    ],
  },
  {
    id: 3, code: "L3", name: "Prospero Bridge",
    summary: "Context switch · TTF calendar · operator-initiated transfers",
    status: "pending",
    metrics: [
      ["active instance", "prosper0"],
      ["last xfer",       "— none"],
      ["ttf calendar",    "not wired"],
    ],
    files: ["bridge/context.py", "bridge/transfer.py", "bridge/ttf_calendar.py"],
  },
  {
    id: 2, code: "L2", name: "Prosper0 Vault",
    summary: "Work-scoped flat-file markdown · surfacing engine · modes",
    status: "pending",
    metrics: [
      ["path",     "~/prosper0/vault (stub)"],
      ["notes",    "3 scaffold · 0 live"],
      ["surfaced", "— engine idle"],
    ],
    files: ["vault/prosper0.py", "vault/surface.py", "vault/modes.py"],
  },
  {
    id: 1, code: "L1", name: "LLM Stack · von Prosper0",
    summary: "Local inference · model-agnostic · MCP wiring · orchestrator",
    status: "nominal",
    metrics: [
      ["model",      "qwen2.5:7b-instruct-q5_K_M"],
      ["runtime",    "ollama · 0.5.4 · docker"],
      ["mem res.",   "5.81 GiB / 16 GiB"],
      ["tokens/s",   "42.7 last, 38.9 avg"],
      ["context",    "4,812 / 32k"],
      ["uptime",     "00:47:12"],
    ],
    files: ["stack/orchestrator.py", "stack/tools.config.yaml", "stack/model.py"],
  },
];

const MODES = [
  { id: "available",  label: "available",  hint: "surfacing on · tools unrestricted" },
  { id: "in-meeting", label: "in-meeting", hint: "read-only · surfacing muted" },
  { id: "deep-work",  label: "deep-work",  hint: "single-task · notifications off" },
  { id: "off-hours",  label: "off-hours",  hint: "vault read-only · no outbound" },
];

const TOOLS = [
  { id: "vault.read",      layer: 2, kind: "read",  allow: true,  note: "markdown only · no symlinks" },
  { id: "vault.write",     layer: 2, kind: "write", allow: true,  note: "confirm on ambiguous path" },
  { id: "ttf.read",        layer: 3, kind: "read",  allow: true,  note: "shared calendar · source-tagged" },
  { id: "bridge.transfer", layer: 3, kind: "net",   allow: true,  note: "operator must send · CC employer" },
  { id: "web.fetch",       layer: 1, kind: "net",   allow: false, note: "disabled by tools.config.yaml" },
  { id: "shell.exec",      layer: 1, kind: "exec",  allow: false, note: "disabled · fail-closed" },
  { id: "model.swap",      layer: 1, kind: "admin", allow: false, note: "operator-only · not AI-editable" },
];

// --- Sample conversation (rendered as if resumed)
const INITIAL_TURNS = [
  {
    id: "t1", role: "operator", t: "09:41:03",
    text: "ariel, summarize what landed yesterday on the enforcement middleware. just the merged stuff."
  },
  {
    id: "t2", role: "ariel", t: "09:41:04",
    text: "Three commits to the enforcement chain merged yesterday. Short form below.",
    tools: [
      { name: "vault.read", path: "prosper0/vault/log/2026-04-20.md",     ms: 41,  bytes: 3812 },
      { name: "vault.read", path: "prosper0/vault/spec/adr-002.md",        ms: 33,  bytes: 6104 },
      { name: "git.log",    path: "stack/middleware/",                     ms: 182, bytes: 1920, args: "--since=24h" },
    ],
    artifact: {
      kind: "list",
      title: "Merged 2026-04-20 · middleware chain",
      items: [
        "fail_closed.py — default-deny wrapper for every tool dispatch",
        "signed_config.py — ed25519 verify on every tools.config.yaml read",
        "audit.py — before/after hooks; tamper-evident via hash chain",
      ],
    },
  },
  {
    id: "t3", role: "operator", t: "09:42:17",
    text: "ok. draft a status note to my manager — two sentences. no specifics, just that the transparency layer is green and what's next."
  },
];

// --- Audit stream (most recent first)
const INITIAL_AUDIT = [
  { id: "a01", t: "09:41:04.318", layer: 1, kind: "tool",    verb: "vault.read",     target: "vault/log/2026-04-20.md", ok: true,  dur: 41 },
  { id: "a02", t: "09:41:04.351", layer: 1, kind: "tool",    verb: "vault.read",     target: "vault/spec/adr-002.md",    ok: true,  dur: 33 },
  { id: "a03", t: "09:41:04.533", layer: 1, kind: "tool",    verb: "git.log",        target: "stack/middleware/",        ok: true,  dur: 182 },
  { id: "a04", t: "09:40:51.004", layer: 4, kind: "verify",  verb: "config.signature", target: "tools.config.yaml",      ok: true,  dur: 8,   note: "ed25519 · employer pubkey" },
  { id: "a05", t: "09:40:02.777", layer: 1, kind: "model",   verb: "load",           target: "qwen2.5:7b-q5_K_M",        ok: true,  dur: 4210, note: "warm start" },
  { id: "a06", t: "09:39:58.110", layer: 4, kind: "deny",    verb: "tool.dispatch",  target: "web.fetch",                ok: false, dur: 0,   note: "disabled by tools.config.yaml" },
  { id: "a07", t: "09:39:40.918", layer: 1, kind: "boot",    verb: "orchestrator",   target: "prosper0-orchestrator",    ok: true,  dur: 612 },
  { id: "a08", t: "09:39:39.402", layer: 4, kind: "verify",  verb: "audit.chain",    target: "audit.log.jsonl",          ok: true,  dur: 14,  note: "hash head matches" },
  { id: "a09", t: "09:39:38.007", layer: 4, kind: "verify",  verb: "vault.isolation",target: "prosper0 ⊥ marlin",        ok: true,  dur: 2,   note: "no shared paths" },
  { id: "a10", t: "09:39:35.001", layer: 6, kind: "info",    verb: "deploy.mode",    target: "host (not usb)",           ok: true,  dur: 0,   note: "portable layer dormant" },
  { id: "a11", t: "09:37:11.220", layer: 3, kind: "info",    verb: "bridge.idle",    target: "no transfers queued",      ok: true,  dur: 0 },
];

// Canned response for the second operator turn (triggers on submit of t3)
const MANAGER_NOTE_TOOLS = [
  { name: "vault.read",     path: "vault/people/manager.md",            ms: 28, bytes: 1104 },
  { name: "vault.read",     path: "vault/status/weekly-template.md",    ms: 22, bytes: 642  },
  { name: "policy.check",   path: "tools.config.yaml § transfer.email", ms:  6, bytes: 0,  args: "scope=outbound-draft" },
];
const MANAGER_NOTE_TEXT =
  "Draft below — two sentences, no specifics. Destination: employer@example.com. I've prepared it but not sent; you need to approve and CC the transparency address.";
const MANAGER_NOTE_ARTIFACT = {
  kind: "draft",
  title: "Draft · status note · to: manager · cc: transparency@",
  body: [
    "Transparency layer is green — enforcement middleware is merged and the full 33-test suite passes clean.",
    "Next up is wiring the vault surfacing engine so I can start giving you same-day progress summaries without you asking.",
  ],
  meta: [
    ["to",     "manager@employer"],
    ["cc",     "transparency@employer (auto, per ADR-004)"],
    ["policy", "self-certification transfer · human-gated send"],
  ],
};

// Running tally (bottom strip)
const SESSION_STATS = {
  started: "09:39:35",
  tools:   { ok: 14, denied: 1, pending: 0 },
  transfers: { drafted: 0, sent: 0 },
  tokens:  { in: 1204, out: 3188 },
  context: { used: 4812, max: 32768 },
};

window.P0 = {
  LAYERS, MODES, TOOLS,
  INITIAL_TURNS, INITIAL_AUDIT,
  MANAGER_NOTE_TOOLS, MANAGER_NOTE_TEXT, MANAGER_NOTE_ARTIFACT,
  SESSION_STATS,
};
