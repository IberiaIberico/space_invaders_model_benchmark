#!/usr/bin/env python3
"""Build index.html linking every <model>/invaders.html with a summary from its meta.json.

Usage:
    python build_index.py [--root .] [--out index.html]

Re-run after each benchmark to refresh the page.
"""

import argparse
import html
import json
from datetime import datetime
from pathlib import Path


def load_meta(folder: Path) -> dict | None:
    path = folder / "meta.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def to_number(value) -> float | None:
    # Agent runs record usage as strings like "64.1k".
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().lower().replace(",", "")
        mult = 1000 if s.endswith("k") else 1_000_000 if s.endswith("m") else 1
        try:
            return float(s.rstrip("km")) * mult
        except ValueError:
            return None
    return None


def summarize(folder: Path, root: Path) -> dict:
    page = folder / "invaders.html"
    meta = load_meta(folder) or {}
    usage = meta.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    source = page.read_text(encoding="utf-8", errors="replace")

    if "prompt_tokens" in usage or "completion_tokens" in usage:
        kind = "local"
        out_tokens = usage.get("completion_tokens")
        in_tokens = usage.get("prompt_tokens")
    elif usage:
        kind = "agent"
        out_tokens = to_number(usage.get("output"))
        in_tokens = to_number(usage.get("input"))
    else:
        kind = "none"
        out_tokens = in_tokens = None

    return {
        "folder": folder.name,
        "href": page.relative_to(root).as_posix(),
        "kind": kind,
        "model": meta.get("model"),
        "provider": meta.get("provider") or ("LM Studio" if kind == "local" else None),
        "timestamp": meta.get("timestamp"),
        "elapsed": meta.get("elapsed_seconds"),
        "finish": meta.get("finish_reason"),
        "tps": meta.get("tokens_per_second"),
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "reasoning_tokens": details.get("reasoning_tokens"),
        "cache_read": to_number(usage.get("cache_read")),
        "cache_write": to_number(usage.get("cache_write")),
        "cost": details.get("total_costs"),
        "temperature": meta.get("temperature"),
        "max_tokens": meta.get("max_tokens"),
        "html_extracted": meta.get("html_extracted"),
        "html_bytes": page.stat().st_size,
        "html_lines": source.count("\n") + 1,
        "has_response": (folder / "response.md").exists(),
        "has_reasoning": (folder / "reasoning.md").exists(),
        "prompt": meta.get("prompt"),
        "system": meta.get("system"),
    }


def index_texts(runs: list[dict], key: str) -> list[str]:
    # Replace each run's text with a 1-based id into a shared list, so a long prompt is shown once.
    texts: list[str] = []
    for r in runs:
        text = r.pop(key)
        if text:
            if text not in texts:
                texts.append(text)
            r[key + "_id"] = texts.index(text) + 1
        else:
            r[key + "_id"] = None
    return texts


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Invaders Bench</title>
<style>
:root {
  --bg: #0b0d10; --panel: #14181d; --line: #262c34; --text: #e6e9ee; --muted: #8a94a3;
  --accent: #39d353; --warn: #e3b341; --bad: #f85149; --local: #58a6ff; --agent: #d2a8ff;
}
@media (prefers-color-scheme: light) {
  :root { --bg: #f6f7f9; --panel: #fff; --line: #dde1e6; --text: #1b1f24; --muted: #5b6573;
          --accent: #1a7f37; --warn: #9a6700; --bad: #cf222e; --local: #0969da; --agent: #8250df; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
       font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
header { padding: 24px 16px 8px; max-width: 1280px; margin: auto; }
h1 { margin: 0; font: 700 22px ui-monospace, Consolas, monospace; letter-spacing: .04em; }
h1 span { color: var(--accent); }
.sub { color: var(--muted); margin-top: 4px; }
.bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 16px; }
.bar input, .bar select { background: var(--panel); color: var(--text); border: 1px solid var(--line);
       border-radius: 6px; padding: 6px 10px; font: inherit; }
.bar input { flex: 1 1 200px; }
main { max-width: 1280px; margin: auto; padding: 8px 16px 40px;
       display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px;
        display: flex; flex-direction: column; gap: 10px; }
.card:hover { border-color: var(--accent); }
.top { display: flex; justify-content: space-between; gap: 8px; align-items: start; }
.name { font: 600 15px ui-monospace, Consolas, monospace; word-break: break-word; color: var(--text);
        text-decoration: none; }
.name:hover { color: var(--accent); }
.model { color: var(--muted); font-size: 12px; word-break: break-word; }
.tag { font-size: 11px; padding: 2px 7px; border-radius: 99px; border: 1px solid; white-space: nowrap; }
.tag.local { color: var(--local); } .tag.agent { color: var(--agent); } .tag.none { color: var(--muted); }
dl { margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 3px 12px; font-size: 13px; }
dt { color: var(--muted); } dd { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }
.ok { color: var(--accent); } .warn { color: var(--warn); } .bad { color: var(--bad); }
.foot { display: flex; gap: 12px; flex-wrap: wrap; font-size: 12px; margin-top: auto; }
.foot a { color: var(--muted); }
.play { margin-left: auto; color: var(--accent) !important; font-weight: 600; }
.empty { color: var(--muted); grid-column: 1 / -1; text-align: center; padding: 40px; }
.prompts { max-width: 1280px; margin: 8px auto 0; padding: 0 16px; display: grid; gap: 8px; }
.prompts details { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; }
.prompts summary { cursor: pointer; padding: 10px 14px; font-weight: 600; }
.prompts summary small { color: var(--muted); font-weight: 400; margin-left: 6px; }
.prompts pre { margin: 0; padding: 0 14px 14px; white-space: pre-wrap; word-break: break-word;
               font: 12.5px/1.5 ui-monospace, Consolas, monospace; color: var(--text); }
.prompts details:target { border-color: var(--accent); }
.ptags { display: flex; gap: 6px; flex-wrap: wrap; }
.ptags a, .ptags span { font-size: 11px; padding: 1px 7px; border-radius: 4px; border: 1px solid var(--line);
                        color: var(--muted); text-decoration: none; }
.ptags a:hover { color: var(--accent); border-color: var(--accent); }
</style>
</head>
<body>
<header>
  <h1>INVADERS <span>BENCH</span></h1>
  <div class="sub">__COUNT__ runs &middot; generated __GENERATED__ by build_index.py</div>
  <div class="bar">
    <input id="q" type="search" placeholder="Filter by folder or model…">
    <select id="kind">
      <option value="">All sources</option>
      <option value="local">Local API (LM Studio / DeepSeek)</option>
      <option value="agent">Agent runs</option>
      <option value="none">No metadata</option>
    </select>
    <select id="sort">
      <option value="folder">Sort: name</option>
      <option value="timestamp">Sort: newest</option>
      <option value="elapsed">Sort: fastest</option>
      <option value="tps">Sort: tokens/s</option>
      <option value="out_tokens">Sort: output tokens</option>
      <option value="html_bytes">Sort: HTML size</option>
    </select>
  </div>
</header>
<section class="prompts" id="prompts"></section>
<main id="grid"></main>
<script>
const RUNS = __DATA__;
const PROMPTS = __PROMPTS__;
const SYSTEMS = __SYSTEMS__;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = n => n == null ? null : n >= 10000 ? (n / 1000).toFixed(1) + "k" : Math.round(n).toLocaleString();
const dur = s => s == null ? null : s >= 60 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${s}s`;
const kb = b => (b / 1024).toFixed(1) + " KB";
const KIND = { local: "local API", agent: "agent", none: "no meta" };

function row(label, value, cls = "") {
  return value == null || value === "" ? "" : `<dt>${label}</dt><dd class="${cls}">${value}</dd>`;
}

function card(r) {
  const finishCls = r.finish === "stop" ? "ok" : r.finish === "length" ? "bad" : "warn";
  const showModel = r.model && r.model.split("/").pop() !== r.folder;
  return `<article class="card">
    <div class="top">
      <div>
        <a class="name" href="${esc(r.href)}">${esc(r.folder)}</a>
        ${showModel ? `<div class="model">${esc(r.model)}</div>` : ""}
      </div>
      <span class="tag ${r.kind}">${r.provider && r.kind === "local" ? esc(r.provider) : KIND[r.kind]}</span>
    </div>
    <dl>
      ${row("Run", r.timestamp ? esc(r.timestamp.replace("T", " ")) : null)}
      ${row("Time", dur(r.elapsed))}
      ${row("Tokens/s", r.tps)}
      ${row("Input tokens", num(r.in_tokens))}
      ${row("Output tokens", num(r.out_tokens))}
      ${row("Reasoning tokens", r.reasoning_tokens ? num(r.reasoning_tokens) : null)}
      ${row("Cache read / write", r.cache_read != null ? `${num(r.cache_read)} / ${num(r.cache_write)}` : null)}
      ${row("Cost", r.cost != null ? "$" + r.cost.toFixed(2) : null)}
      ${row("Finish", r.finish ? esc(r.finish) : null, finishCls)}
      ${row("Temp / max", r.temperature != null ? `${r.temperature} / ${num(r.max_tokens)}` : null)}
      ${row("HTML", `${kb(r.html_bytes)} · ${r.html_lines.toLocaleString()} lines`)}
    </dl>
    <div class="ptags">
      ${r.prompt_id ? `<a href="#prompt-${r.prompt_id}">Prompt #${r.prompt_id}</a>` : `<span>Prompt unknown</span>`}
      ${r.system_id ? `<a href="#system-${r.system_id}">System #${r.system_id}</a>` : `<span>No system prompt</span>`}
    </div>
    <div class="foot">
      ${r.kind !== "none" ? `<a href="${esc(r.folder)}/meta.json">meta.json</a>` : ""}
      ${r.has_response ? `<a href="${esc(r.folder)}/response.md">response</a>` : ""}
      ${r.has_reasoning ? `<a href="${esc(r.folder)}/reasoning.md">reasoning</a>` : ""}
      <a class="play" href="${esc(r.href)}">Play ▶</a>
    </div>
  </article>`;
}

function render() {
  const q = $("#q").value.toLowerCase(), kind = $("#kind").value, key = $("#sort").value;
  const asc = key === "folder" || key === "elapsed";
  const list = RUNS
    .filter(r => (!kind || r.kind === kind) &&
                 (r.folder + " " + (r.model || "")).toLowerCase().includes(q))
    .sort((a, b) => {
      const x = a[key], y = b[key];
      if (x == null) return 1;
      if (y == null) return -1;
      if (typeof x === "string") return asc ? x.localeCompare(y) : y.localeCompare(x);
      return asc ? x - y : y - x;
    });
  $("#grid").innerHTML = list.map(card).join("") || `<div class="empty">No runs match.</div>`;
}

function promptBlock(kind, label, text, i) {
  const users = RUNS.filter(r => r[kind + "_id"] === i + 1).map(r => r.folder);
  return `<details id="${kind}-${i + 1}">
    <summary>${label} #${i + 1}<small>${text.length.toLocaleString()} chars · used by ${users.length} run${users.length === 1 ? "" : "s"}</small></summary>
    <pre>${esc(text)}</pre>
    <pre class="model">Runs: ${esc(users.join(", "))}</pre>
  </details>`;
}

$("#prompts").innerHTML =
  PROMPTS.map((t, i) => promptBlock("prompt", "Prompt", t, i)).join("") +
  SYSTEMS.map((t, i) => promptBlock("system", "System prompt", t, i)).join("");
// Jumping from a card's tag opens the matching prompt.
addEventListener("hashchange", () => { const d = document.getElementById(location.hash.slice(1)); if (d) d.open = true; });

["#q", "#kind", "#sort"].forEach(s => $(s).addEventListener("input", render));
render();
</script>
</body>
</html>
"""


def to_script_json(value) -> str:
    # "</" inside the JSON would end the <script> block early.
    return json.dumps(value, indent=1).replace("</", "<\\/")


def build_index(root: Path, out: Path | None = None) -> Path:
    root = root.resolve()
    out = out or root / "index.html"

    runs = [summarize(d, root) for d in sorted(root.iterdir(), key=lambda p: p.name.lower())
            if d.is_dir() and (d / "invaders.html").exists()]
    prompts = index_texts(runs, "prompt")
    systems = index_texts(runs, "system")

    page = (PAGE.replace("__DATA__", to_script_json(runs))
                .replace("__PROMPTS__", to_script_json(prompts))
                .replace("__SYSTEMS__", to_script_json(systems))
                .replace("__COUNT__", str(len(runs)))
                .replace("__GENERATED__", html.escape(datetime.now().strftime("%Y-%m-%d %H:%M"))))
    out.write_text(page, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).parent, help="Folder holding the model folders")
    parser.add_argument("--out", type=Path, help="Output file (default <root>/index.html)")
    args = parser.parse_args()
    out = build_index(args.root, args.out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
