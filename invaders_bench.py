#!/usr/bin/env python3
"""Ask an LM Studio (or DeepSeek) model to build Space Invaders in HTML and save the result.

Usage:
    python invaders_bench.py <model> [--prompt-file prompt.txt] [--url http://localhost:1234/v1]
    python invaders_bench.py [deepseek-chat|deepseek-reasoner] --deepseek-key sk-...
    python invaders_bench.py --deepseek-key        # key taken from DEEPSEEK_API_KEY

The HTML returned by the model is written to ./<model_folder>/invaders.html,
along with the raw response and run metadata for later comparison.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_URL = "http://localhost:1234/v1"
DEEPSEEK_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"
DEFAULT_MAX_TOKENS = 32000
# DeepSeek rejects max_tokens above the model's output limit.
DEEPSEEK_MAX_TOKENS = {"deepseek-chat": 8192, "deepseek-reasoner": 65536}
DEFAULT_SYSTEM = (
    "You are an expert web game developer. Reply with a single, complete, "
    "self-contained HTML file (inline CSS and JavaScript, no external assets). "
    "Output only the HTML inside one ```html code block."
)
# Placeholder until the real prompt is provided via --prompt / --prompt-file.
DEFAULT_PROMPT = (
    "Create a complete Space Invaders-style arcade game using only HTML5, CSS and vanilla JavaScript."
    ""
    " "
    ""
    "Goal:"
    "Reproduce the gameplay, visual style and feel of the original 1978 Space Invaders arcade game as closely as reasonably possible."
    ""
    " "
    ""
    "Technical requirements:"
    "- Deliver everything in a single self-contained index.html file."
    "- No external libraries, frameworks, images, fonts or dependencies."
    "- Use HTML5 Canvas for rendering."
    "- The file must run directly in a modern browser."
    "- Keep the implementation compact, clean and efficient."
    "- Do not explain the code."
    "- Output ONLY the complete HTML file."
    ""
    " "
    ""
    "Gameplay:"
    "- Player cannon at the bottom, moving left/right."
    "- Controls: Left/Right arrows or A/D. Space to shoot."
    "- Player can have only one shot on screen at a time, like the original."
    "- Formation of alien invaders arranged in rows."
    "- Different alien types/appearances by row."
    "- Aliens move horizontally as a group, reverse direction and descend when reaching an edge."
    "- Alien movement progressively speeds up as aliens are destroyed."
    "- Aliens fire downward at the player."
    "- Implement the characteristic accelerating rhythm/pacing of Space Invaders."
    "- Four destructible defensive shields/bunkers between player and invaders."
    "- Both player shots and alien shots must progressively damage the shields."
    "- UFO/mystery ship occasionally crosses the top of the screen."
    "- Score system."
    "- Lives system."
    "- Wave progression: after destroying all aliens, start a new wave."
    "- Game over when the player loses all lives or invaders reach the bottom."
    ""
    " "
    ""
    "Visual style:"
    "- Faithful 1978 arcade aesthetic."
    "- Black background."
    "- Pixel-art appearance."
    "- Aliens, player, UFO, shields and projectiles should resemble the classic silhouettes, but draw them programmatically rather than using external assets."
    "- Crisp pixels, no antialiasing/blurring."
    "- Retro arcade score/lives display."
    "- Fixed logical game resolution scaled to fit the browser while preserving aspect ratio."
    ""
    " "
    ""
    "Sound:"
    "- Generate simple retro sounds with the Web Audio API."
    "- Alien movement rhythm."
    "- Player shot."
    "- Alien destroyed."
    "- Player explosion."
    "- UFO sound."
    ""
    " "
    ""
    "Architecture:"
    "- Use requestAnimationFrame for the main loop."
    "- Separate update/render logic."
    "- Use delta time where appropriate."
    "- Avoid unnecessary abstractions and comments."
    "- Prioritize gameplay fidelity over visual effects."
    ""
    " "
    ""
    "Important:"
    "Before writing the code, internally plan the implementation, but do not output the plan."
    "Return ONLY the final contents of index.html inside one code block."
    "Do not include explanations before or after it."
    ""
    " "
    ""
    "I want you to test and save as spaceinvaders.html in the project folder."
)


def auth_headers(api_key: str | None) -> dict:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def list_models(base_url: str, api_key: str | None = None) -> list[str]:
    req = urllib.request.Request(f"{base_url}/models", headers=auth_headers(api_key))
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    return [m["id"] for m in data.get("data", [])]


def chat(base_url: str, model: str, system: str, prompt: str,
         temperature: float, max_tokens: int, timeout: int,
         api_key: str | None = None) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **auth_headers(api_key)},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def extract_html(text: str) -> str | None:
    # Drop reasoning blocks some models emit (e.g. Qwen/DeepSeek <think>...</think>).
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Prefer fenced code blocks; pick the largest one that looks like HTML.
    blocks = re.findall(r"```[ \t]*([\w-]*)[^\n]*\n(.*?)```", text, flags=re.DOTALL)
    html_blocks = [body for lang, body in blocks
                   if lang.lower() in ("html", "htm") or "<html" in body.lower()]
    if html_blocks:
        return max(html_blocks, key=len).strip()

    # Fall back to a raw document in the response body.
    match = re.search(r"(<!DOCTYPE html.*?</html>|<html.*?</html>)", text,
                      flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def folder_name(model: str) -> str:
    # "qwen/qwen3-coder-30b" -> "qwen3-coder-30b"; keep it filesystem-safe.
    name = model.rstrip("/").split("/")[-1]
    return re.sub(r"[^\w.-]+", "_", name).strip("._") or "model"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", nargs="?",
                        help=f"Model id as shown by LM Studio (with --deepseek-key defaults to {DEEPSEEK_DEFAULT_MODEL})")
    parser.add_argument("--prompt", help="Prompt text (overrides the default)")
    parser.add_argument("--prompt-file", type=Path, help="Read prompt from a file")
    parser.add_argument("--system", default=DEFAULT_SYSTEM, help="System prompt")
    parser.add_argument("--url", help=f"API base URL (default {DEFAULT_URL}, or {DEEPSEEK_URL} with --deepseek-key)")
    parser.add_argument("--deepseek-key", nargs="?", const=os.environ.get("DEEPSEEK_API_KEY", ""),
                        metavar="KEY", help="Use the DeepSeek API with this token "
                                            "(omit KEY to read DEEPSEEK_API_KEY)")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent, help="Output root directory")
    parser.add_argument("--folder", help="Output folder name (default derived from model id)")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int,
                        help=f"Max output tokens (default {DEFAULT_MAX_TOKENS}, capped to the DeepSeek model limit)")
    parser.add_argument("--timeout", type=int, default=1800, help="Request timeout in seconds")
    parser.add_argument("--list", action="store_true", help="List models available on the API and exit")
    parser.add_argument("--no-index", action="store_true", help="Don't rebuild index.html after the run")
    args = parser.parse_args()

    use_deepseek = args.deepseek_key is not None
    if use_deepseek and not args.deepseek_key:
        parser.error("--deepseek-key needs a token or the DEEPSEEK_API_KEY environment variable")
    api_key = args.deepseek_key if use_deepseek else None
    provider = "DeepSeek" if use_deepseek else "LM Studio"
    base_url = (args.url or (DEEPSEEK_URL if use_deepseek else DEFAULT_URL)).rstrip("/")

    if args.list:
        try:
            for model_id in list_models(base_url, api_key):
                print(model_id)
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
            return 1
        except urllib.error.URLError as e:
            print(f"Cannot reach {provider} at {base_url}: {e}", file=sys.stderr)
            return 1
        return 0

    if not args.model:
        if not use_deepseek:
            parser.error("model is required (use --list to see available models)")
        args.model = DEEPSEEK_DEFAULT_MODEL

    max_tokens = args.max_tokens or DEFAULT_MAX_TOKENS
    if use_deepseek and args.model in DEEPSEEK_MAX_TOKENS:
        max_tokens = min(max_tokens, DEEPSEEK_MAX_TOKENS[args.model])

    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    else:
        prompt = args.prompt or DEFAULT_PROMPT

    out_dir = args.out / (args.folder or folder_name(args.model))
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Model:  {args.model} ({provider})")
    print(f"Output: {out_dir}")
    print("Waiting for response...", flush=True)

    start = time.monotonic()
    try:
        result = chat(base_url, args.model, args.system, prompt,
                      args.temperature, max_tokens, args.timeout, api_key)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Cannot reach {provider} at {base_url}: {e}", file=sys.stderr)
        return 1
    except TimeoutError:
        print(f"Request timed out after {args.timeout}s", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - start

    choice = result["choices"][0]
    content = choice["message"].get("content") or ""
    # deepseek-reasoner returns its chain of thought separately from the answer.
    reasoning = choice["message"].get("reasoning_content")
    usage = result.get("usage", {})

    (out_dir / "response.md").write_text(content, encoding="utf-8")
    if reasoning:
        (out_dir / "reasoning.md").write_text(reasoning, encoding="utf-8")

    html = extract_html(content)
    meta = {
        "model": args.model,
        "provider": provider,
        "base_url": base_url,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed, 1),
        "finish_reason": choice.get("finish_reason"),
        "usage": usage,
        "tokens_per_second": round(usage["completion_tokens"] / elapsed, 1)
        if usage.get("completion_tokens") and elapsed else None,
        "temperature": args.temperature,
        "max_tokens": max_tokens,
        "html_extracted": html is not None,
        "system": args.system,
        "prompt": prompt,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Done in {elapsed:.1f}s, finish_reason={choice.get('finish_reason')}, usage={usage}")
    if choice.get("finish_reason") == "length":
        print("Warning: response hit max_tokens and may be truncated.", file=sys.stderr)

    if html is None:
        print(f"No HTML found in response. Raw output saved to {out_dir / 'response.md'}", file=sys.stderr)
        return 2

    html_path = out_dir / "invaders.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"Saved {html_path}")

    if not args.no_index:
        # A broken index page shouldn't fail an otherwise successful run.
        try:
            from build_index import build_index
            print(f"Updated {build_index(args.out)}")
        except Exception as e:
            print(f"Warning: could not rebuild index.html: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())