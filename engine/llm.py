"""Thin wrapper over the hyper.charm.land OpenAI-compatible endpoint.

Two roles are used across the pipeline:
  PRO   - topic selection, outline audit, review, final approval (better judgement)
  FLASH - research synthesis, outlining, drafting, rewriting (high volume)
A third pool (JUDGES) scores whether a text reads as AI-written. Since 2026-08-22
it is simply PRO and FLASH — the models the user picked — and nothing ever
substitutes another model behind their back.

``AW_BACKEND`` is an ordered chain, not a single name: ``claude,hyper,go``
means "Claude Code CLI, and if it fails, hyper, and if that fails too, go".
Each provider carries its own catalogue, so the roles are translated as the call
walks down the chain — PRO on ``claude`` is ``opus``, PRO on ``hyper`` is
``qwen3.8-max``. Pick it interactively in the wizard, with ``--proveedor`` /
``--pro`` / ``--flash`` / ``--respaldo``, or in ``.env``.

The judges never follow the chain into ``claude``: an exclusive provider only
ever serves models from its own catalogue.
"""

from __future__ import annotations

import atexit
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any

from openai import OpenAI

import ui

# On Windows, subprocess.run() and blocking network I/O swallow Ctrl+C because
# Python defers signal delivery until the C call returns. This handler raises
# immediately so the user never waits for a 660s LLM call to finish before the
# interrupt lands.
if sys.platform == "win32":
    def _sigint_handler(sig, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, _sigint_handler)

BASE_URL = os.environ.get("AW_BASE_URL", "https://hyper.charm.land/v1")

# Fallback path: `opencode run -m opencode-go/<model>`. Version suffixes are a
# hyper-ism (deepseek-v4-pro-0813); opencode-go carries the unsuffixed name.
# The CLI route is pinned to go; zen is already a first-class provider on its own.
OPENCODE_PROVIDER = "opencode-go"

# Claude Code takes the short aliases; anything else is passed through, so a full
# id (claude-opus-5) also works.
CLAUDE_ALIAS = {"pro": "opus", "flash": "sonnet",
                "qwen3.8-max": "opus", "deepseek-v4-pro-0813": "sonnet"}

OPENCODE_ALIAS = {
    "deepseek-v4-pro-0813": "deepseek-v4-pro",
    "deepseek-v4-flash-0731": "deepseek-v4-flash",
}

# `opencode run` defaults to the `build` agent: the whole coding toolbox, plus
# CLAUDE.md and every plugin skill in the system prompt. Measured 2026-08-22, on a
# section-sized prompt deepseek answered with six rounds of tool calls and not one
# word of prose. `redactor` is defined in opencode.json with no tools and a
# one-line system prompt, which is what a drafting call actually needs.
OPENCODE_AGENT = os.environ.get("AW_OPENCODE_AGENT", "redactor")

# opencode-go/deepseek-v4-pro streams for ~40s and then returns nothing at all
# above ~47k characters of prompt: no text, no error event, zero tokens billed,
# exit code 0. Its flash sibling answers the very same prompt, so an empty pro run
# retries there instead of killing the last link of the chain. Measured 2026-08-22
# on the 52k-character section prompt; 46k still works on pro.
OPENCODE_SIBLING = {"deepseek-v4-pro": "deepseek-v4-flash"}

ROOT = pathlib.Path(__file__).resolve().parent

# openai-oauth runs a local proxy that handles ChatGPT OAuth login and exposes
# an OpenAI-compatible /v1 surface. The proxy is started on demand via npx.
_OAUTH_PORT = 10531
_OAUTH_BASE_URL = f"http://127.0.0.1:{_OAUTH_PORT}/v1"

# Estimated API-equivalent costs (USD per million tokens: input/output) and the
# minimum ChatGPT tier that serves each model. Used to show value in the wizard.
_OAUTH_COSTS: dict[str, tuple[float, float, str]] = {
    "gpt-5.6-sol":    (4.0, 20.0, "Plus $20"),
    "gpt-5.6-terra":  (2.0, 10.0, "Plus $20"),
    "gpt-5.6-luna":   (0.5, 2.0,  "Free"),
    "gpt-5.5-instant": (1.0, 4.0, "Plus $20"),
    "gpt-5.5-thinking": (3.0, 12.0, "Plus $20"),
    "gpt-5.4":        (2.5, 10.0, "Pro $100"),
    "gpt-5.4-mini":   (0.15, 0.6, "Plus $20"),
    "o3":             (10.0, 40.0, "Pro $100"),
    "o3-mini":        (1.1, 4.4,  "Plus $20"),
    "o4-mini":        (1.1, 4.4,  "Plus $20"),
}
# Subscription tiers: (name, USD/month, usage multiplier vs Plus)
_OAUTH_TIERS = [
    ("Free", 0, 1),
    ("Go", 8, 1),
    ("Plus", 20, 1),
    ("Pro $100", 100, 5),
    ("Pro $200", 200, 20),
]


def _oauth_proxy_running() -> bool:
    import socket
    try:
        with socket.create_connection(("127.0.0.1", _OAUTH_PORT), timeout=1):
            return True
    except OSError:
        return False


def ensure_oauth_proxy() -> None:
    """Start the openai-oauth proxy if it is not already listening."""
    if _oauth_proxy_running():
        return
    # On Windows npx is a .cmd: Popen(["npx", …]) raises [WinError 2] even though
    # the shell finds it, so hand Popen the path shutil.which resolved.
    exe = shutil.which("npx")
    if not exe:
        raise FileNotFoundError(
            "npx no está en el PATH; instalá Node.js para usar el proveedor oauth")
    ui.log("[llm] arrancando proxy openai-oauth…")
    subprocess.Popen(
        [exe, "openai-oauth@latest", "--detach"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    for _ in range(40):
        if _oauth_proxy_running():
            return
        time.sleep(0.25)
    raise RuntimeError("el proxy openai-oauth no arrancó en 10s; "
                       "verificá que npx y node estén instalados")


def oauth_cost_label(model: str) -> str:
    """Estimated API-equivalent cost and subscription tier for an oauth model."""
    entry = _OAUTH_COSTS.get(model.lower())
    if not entry:
        return ""
    inp, out, tier = entry
    return f"~${inp:.2f}/${out:.2f} por Mtok (API) · requiere {tier}"


def oauth_value_summary() -> str:
    """One-line value estimate: what the subscription buys vs. paying per token."""
    # A typical article run costs ~100k tokens; at Sol rates that is ~$1.20.
    # 25 articles/month ≈ $30 at API rates vs $20 for Plus.
    return ("Plus $20/mo ≈ $30/mo en tokens a precio API para ~25 artículos; "
            "Pro $100 da 5× el límite y Sol Pro")

_HYPER_MODELS = ["qwen3.8-max", "qwen3.7-max", "deepseek-v4-pro-0813",
                 "deepseek-v4-flash-0731", "glm-5.2", "glm-5.3-flash",
                 "kimi-k3", "minimax-m3"]

_ZEN_BASE_URL = os.environ.get("AW_ZEN_URL", "https://opencode.ai/zen/v1")
# Zen routes each family server-side; the OpenAI-compatible /v1 surface carries
# these ids (the GPT/Gemini/Claude ones speak /responses and /messages instead).
_ZEN_MODELS = ["qwen3.8-max", "qwen3.7-max", "qwen3.7-plus",
               "deepseek-v4-pro", "deepseek-v4-flash",
               "glm-5.2", "glm-5.1", "glm-5.3-flash", "kimi-k3", "kimi-k2.6", "minimax-m3",
               "big-pickle", "x-preview-f-free"]
ZEN_ALIAS = {"deepseek-v4-pro-0813": "deepseek-v4-pro",
              "deepseek-v4-flash-0731": "deepseek-v4-flash"}

_GROK_BASE_URL = os.environ.get("AW_GROK_URL", "https://api.x.ai/v1")
_GROK_MODELS = ["grok-4", "grok-4-fast", "grok-3", "grok-3-mini"]

# exclusive: the provider only serves models from its own catalogue, so a call
# for a model it does not know skips it and walks on down the chain. That is what
# keeps the judges off Claude when Claude is doing the writing.
PROVIDERS: dict[str, dict] = {
    "claude": {"label": "Claude Code CLI — corre en tu suscripción, sin clave",
               "pro": "opus", "flash": "sonnet", "exclusive": True,
               "alias": CLAUDE_ALIAS,
               "models": ["opus", "sonnet", "haiku",
                          "claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"]},
    "hyper":  {"label": "hyper.charm.land — API OpenAI-compatible (AW_API_KEY)",
               "pro": "qwen3.8-max", "flash": "deepseek-v4-pro-0813",
               "exclusive": False, "alias": {}, "models": _HYPER_MODELS,
               "base_url": BASE_URL, "key_env": "AW_API_KEY"},
    "zen":    {"label": "OpenCode Zen — API directa de opencode.ai/zen (OPENCODE_API_KEY)",
               "pro": "qwen3.8-max", "flash": "deepseek-v4-pro",
               # gpt/gemini/claude ids on zen speak /responses and /messages,
               # not the chat-completions surface this module uses.
               "skip_live": r"^(gpt|gemini|claude|o\d)",
               "exclusive": False, "alias": ZEN_ALIAS, "models": _ZEN_MODELS,
               "base_url": _ZEN_BASE_URL, "key_env": "OPENCODE_API_KEY"},
    "grok":   {"label": "xAI Grok — API directa de x.ai (XAI_API_KEY)",
               "pro": "grok-4", "flash": "grok-4-fast",
               "exclusive": False, "alias": {}, "models": _GROK_MODELS,
               "base_url": _GROK_BASE_URL, "key_env": "XAI_API_KEY"},
    "go": {"label": "opencode CLI local — contra opencode-go",
           "pro": "qwen3.8-max", "flash": "deepseek-v4-pro-0813",
           "exclusive": False, "alias": OPENCODE_ALIAS, "models": _HYPER_MODELS},
    "oauth":  {"label": "openai-oauth — proxy local con tu cuenta de ChatGPT",
               "pro": "gpt-5.6-terra", "flash": "gpt-5.6-terra",
               "exclusive": True, "alias": {},
               "models": ["gpt-5.6-terra", "gpt-5.4", "gpt-5.4-mini",
                          "o3", "o3-mini", "o4-mini"],
               "base_url": _OAUTH_BASE_URL},
}


_catalogue_cache: dict[str, list[str]] = {}


# The CLI route used to be called `opencode`; .env files still say so, and
# silently dropping the name there would lose the chain's last link.
def _canon(backend: str) -> str:
    return "go" if backend == "opencode" else backend


def set_models(backend: str, pro: str = "", flash: str = "") -> None:
    """Override a provider's own PRO/FLASH pair — the models it answers with when
    it is a *backup*. `_as()` reads the pair straight off the spec, so writing it
    here is the whole mechanism."""
    spec = PROVIDERS[backend]
    if pro:
        spec["pro"] = pro
    if flash:
        spec["flash"] = flash


def parse_models(raw: str) -> dict[str, tuple[str, str]]:
    """`hyper:qwen3.8-max/deepseek-v4-pro-0813,zen:glm-5.2/deepseek-v4-pro`.

    FLASH may be omitted (`zen:glm-5.2`); an unknown provider is ignored rather
    than raising, because this also parses a hand-edited .env line.
    """
    out: dict[str, tuple[str, str]] = {}
    for chunk in raw.split(","):
        backend, _, pair = chunk.strip().partition(":")
        backend = _canon(backend.strip().lower())
        if backend not in PROVIDERS or not pair.strip():
            continue
        pro, _, flash = pair.partition("/")
        out[backend] = (pro.strip(), flash.strip())
    return out


for _b, (_pro, _flash) in parse_models(os.environ.get("AW_MODELS", "")).items():
    set_models(_b, _pro, _flash)


def _default_chain() -> list[str]:
    raw = os.environ.get("AW_BACKEND", "hyper")
    chain = [_canon(b.strip().lower()) for b in raw.split(",")]
    chain = [b for b in chain if b in PROVIDERS]
    # go has always been the implicit last resort; AW_OPENCODE_FALLBACK=0
    # is the old switch that turns it off, and it still does.
    if (len(chain) == 1 and "go" not in chain
            and os.environ.get("AW_OPENCODE_FALLBACK", "1") != "0"):
        chain.append("go")
    return chain or ["hyper", "go"]


CHAIN = _default_chain()
PRO = os.environ.get("AW_MODEL_PRO") or PROVIDERS[CHAIN[0]]["pro"]
FLASH = os.environ.get("AW_MODEL_FLASH") or PROVIDERS[CHAIN[0]]["flash"]


def _judges() -> list[str]:
    # The gate is judged by the very models the user configured, in that order,
    # and never by a stand-in: evaluation must not steer off PRO/FLASH.
    return list(dict.fromkeys([PRO, FLASH]))


JUDGES = _judges()


def configure(chain: list[str] | None = None, pro: str = "", flash: str = "",
              models: dict[str, tuple[str, str]] | None = None) -> None:
    """Repoint the router at runtime — what the wizard and the CLI flags call.

    Models default to the head provider's own pair, so switching provider without
    naming models does the sensible thing instead of sending `opus` to hyper.
    """
    global CHAIN, PRO, FLASH, JUDGES
    for backend, (p, f) in (models or {}).items():
        set_models(backend, p, f)
    if chain:
        picked = [_canon(b) for b in chain if _canon(b) in PROVIDERS]
        if not picked:
            raise ValueError(f"proveedor desconocido: {chain}")
        CHAIN = list(dict.fromkeys(picked))
    PRO = pro or PROVIDERS[CHAIN[0]]["pro"]
    FLASH = flash or PROVIDERS[CHAIN[0]]["flash"]
    JUDGES = _judges()
    _clients.clear()               # base_url/key may differ for the new head


def _serves(backend: str, model: str) -> bool:
    prov = PROVIDERS[backend]
    return (model in (PRO, FLASH) or not prov["exclusive"]
            or model in prov["models"])


def _as(backend: str, model: str) -> str:
    """The name this provider knows the model by."""
    prov = PROVIDERS[backend]
    # Role translation is for backups only: the head provider got PRO/FLASH by
    # their literal ids straight from its own catalogue, so a picked model
    # (x-preview-f-free) must not be swapped back to the default (qwen3.7-max).
    if backend != CHAIN[0]:
        if model == PRO:
            model = prov["pro"]
        elif model == FLASH:
            model = prov["flash"]
    # Alias last, not instead: opencode's catalogue is spelled the hyper way, so
    # the role lands on `deepseek-v4-pro-0813` and still needs unsuffixing.
    return prov["alias"].get(model, model)


def describe() -> str:
    backups = " ".join(f"{b}={PROVIDERS[b]['pro']}/{PROVIDERS[b]['flash']}"
                       for b in CHAIN[1:])
    judges = "juez" if len(JUDGES) == 1 else "jueces"
    return (f"{' → '.join(CHAIN)} | PRO={PRO} FLASH={FLASH}"
            + (f" | respaldos: {backups}" if backups else "")
            + f" | {judges}={', '.join(JUDGES)}")


def _live_models(backend: str) -> list[str]:
    """Model ids the provider serves right now, [] if it cannot be asked."""
    spec = PROVIDERS[backend]
    try:
        if backend == "go":
            exe = shutil.which("opencode")
            if not exe:
                return []
            proc = subprocess.run([exe, "models"], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=30)
            # The suffixed hyper-spelling is a go-ism; unsuffix back to the
            # catalogue's names.
            rev = {v: k for k, v in OPENCODE_ALIAS.items()}
            prefix = OPENCODE_PROVIDER + "/"
            return [rev.get(t[len(prefix):], t[len(prefix):])
                    for line in proc.stdout.splitlines() for t in line.split()
                    if t.startswith(prefix)]
        if backend == "oauth":
            if not _oauth_proxy_running():
                return []
        base = spec.get("base_url")
        if not base:
            return []
        import requests
        key = _key_for(spec)
        r = requests.get(base.rstrip("/") + "/models",
                         headers={"Authorization": f"Bearer {key}"} if key else {},
                         timeout=15)
        ids = [str(m["id"]) for m in r.json().get("data", []) if m.get("id")]
        skip = spec.get("skip_live")   # families this endpoint serves another way
        return [i for i in ids if not (skip and re.search(skip, i))]
    except Exception:  # noqa: BLE001 - a dead catalogue degrades to the built-in list
        return []


def catalogue(backend: str) -> list[str]:
    """Every model the provider offers: the built-in list plus whatever its
    /models endpoint (or CLI) answers right now.

    The built-in lists go stale the week a new model ships, and a model name a
    provider does not know is a 404 — so the wizard offers the live list merged
    over the built-in one, deduped, built-ins first.

    When the live list answers it is also the truth about what still exists:
    built-ins the provider dropped are pruned instead of sitting at the top of
    the wizard menu forever (zen removed qwen3.7-max server-side while its own
    default still pointed at it — every default pick 401'd). A dead catalogue
    degrades to the untouched built-in list.
    """
    if backend not in _catalogue_cache:
        built = list(PROVIDERS[backend]["models"])
        live = _live_models(backend)
        if live:
            living = set(live)
            built = [m for m in built if m in living]
            live = sorted(living.difference(built))
        _catalogue_cache[backend] = built + live
    return _catalogue_cache[backend]


_clients: dict[str, OpenAI] = {}


def _opencode_auth_key() -> str:
    """The key opencode's CLI already stores at login — the same one zen needs.
    Crush and every opencode tool read it here, so the script may too instead of
    demanding a duplicate OPENCODE_API_KEY in .env."""
    p = pathlib.Path.home() / ".local" / "share" / "opencode" / "auth.json"
    try:
        auth = json.loads(p.read_text(encoding="utf-8"))
        for name in ("opencode-zen", "opencode", "opencode-go"):
            entry = auth.get(name) or {}
            if entry.get("type") == "api" and entry.get("key"):
                return str(entry["key"])
    except Exception:  # noqa: BLE001 - no auth file is just no fallback
        pass
    return ""


def _key_for(spec: dict) -> str:
    # A custom endpoint must never inherit a different provider's credential.
    if spec.get("own_key_only"):
        return os.environ.get(spec.get("key_env", ""), "")
    # The oauth proxy handles real auth; the OpenAI client just needs a non-empty
    # bearer so it does not refuse to initialise.
    if spec.get("base_url") == _OAUTH_BASE_URL:
        return "openai-oauth"
    # Zen before the shared fallbacks: AW_API_KEY is hyper's key and a wrong
    # bearer here looks like a dead provider instead of a misrouted credential.
    if spec.get("key_env") == "OPENCODE_API_KEY":
        key = os.environ.get("OPENCODE_API_KEY") or _opencode_auth_key()
        if key:
            return key
    return (os.environ.get(spec.get("key_env", ""))
            or os.environ.get("AW_API_KEY")
            or os.environ.get("OPENAI_API_KEY"))


def client(backend: str = "hyper") -> OpenAI:
    c = _clients.get(backend)
    if c is None:
        spec = PROVIDERS[backend]
        if spec.get("base_url") == _OAUTH_BASE_URL:
            ensure_oauth_proxy()
        key = _key_for(spec)
        if not key:
            # RuntimeError, not SystemExit: this provider may be one link in a
            # chain, and a missing key here has to let the next one try.
            raise RuntimeError(f"falta la clave para {backend}: poné "
                               f"{spec.get('key_env', 'AW_API_KEY')}=sk-... in lamplight/.env")
        # 300s is generous for a section-sized completion; past that the upstream
        # has stalled and retrying beats waiting. Raise with AW_TIMEOUT for books.
        timeout = float(os.environ.get("AW_TIMEOUT", "300"))
        c = OpenAI(api_key=key, base_url=spec.get("base_url", BASE_URL),
                   timeout=timeout, max_retries=0)
        _clients[backend] = c
    return c


def _opencode_once(exe: str, target: str, body: str,
                   timeout: int) -> tuple[str, list[str]]:
    """One `opencode run`, returning (text, diagnostics).

    The CLI reports an upstream refusal as an ``error`` event on stdout and still
    exits 0, so the diagnostics are collected here instead of being thrown away —
    a silent empty transcript is the one failure mode that used to reach the caller.
    """
    # The prompt goes through stdin, never argv: Windows caps a command line at
    # 32k characters and a dossier-sized prompt blows past it ("The command line
    # is too long"). `opencode run` with no positional message reads stdin.
    # No --pure: it disables the plugins that register the opencode-go provider,
    # and the run then returns an empty transcript.
    # The coding project's CLAUDE.md forces Spanish and injects coding instructions
    # into article completions. Keep providers/agent settings in an isolated directory.
    config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    config.pop("instructions", None)
    with tempfile.TemporaryDirectory(prefix="lamplight-") as workdir:
        (pathlib.Path(workdir) / "opencode.json").write_text(json.dumps(config), encoding="utf-8")
        proc = subprocess.run(
            [exe, "run", "-m", target, "--agent", OPENCODE_AGENT, "--format", "json"],
            input=body, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, cwd=workdir)
    chunks, notes = [], []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind, part = event.get("type"), event.get("part", {})
        if kind == "text":
            chunks.append(part.get("text", ""))
        elif kind == "error":
            err = event.get("error", {})
            notes.append(f"{err.get('name', 'error')}: "
                         f"{err.get('data', {}).get('message', '')[:200]}")
        elif kind == "step_finish" and part.get("reason") not in (None, "stop"):
            notes.append(f"corte por «{part.get('reason')}» "
                         f"(tokens {part.get('tokens', {}).get('input', 0)})")
    return "".join(chunks).strip(), notes


def opencode_chat(model: str, prompt: str, system: str | None = None,
                  timeout: int | None = None) -> str:
    """Backup path through the opencode CLI. Used only when hyper is down.

    Nothing streams here — one fresh process per completion — so a slow reasoning
    model spends the whole wait silent. `AW_OPENCODE_TIMEOUT` raises the 900s
    allowance for exactly that case.
    """
    if timeout is None:
        timeout = int(os.environ.get("AW_OPENCODE_TIMEOUT", "900"))
    exe = shutil.which("opencode")
    if not exe:
        raise RuntimeError("opencode no está instalado; no hay ruta de respaldo")
    name = OPENCODE_ALIAS.get(model, model)
    body = f"{system}\n\n{prompt}" if system else prompt
    tried: list[str] = []
    for candidate in (name, OPENCODE_SIBLING.get(name)):
        if not candidate:
            break
        target = f"{OPENCODE_PROVIDER}/{candidate}"
        out, notes = _opencode_once(exe, target, body, timeout)
        if out:
            if tried:
                print(f"[llm] opencode: {tried[0].split(':')[0]} volvió vacío; "
                      f"respondió {target}")
            return out
        tried.append(f"{target}: {'; '.join(notes) or 'transcripción vacía'}")
    raise RuntimeError("opencode no devolvió texto — " + " | ".join(tried))


# Claude Code prints a quota notice on **stdout and exits 0**, so it arrives
# looking exactly like a completion: «You've hit your session limit · resets
# 9:10am». It got drafted into the article and parsed as JSON. The length guard
# is what keeps an article that discusses limits from being thrown away — a
# quota notice is one line, never a section.
_QUOTA = re.compile(r"(?i)(session|usage|rate) limit|limit reached|"
                    r"resets? (at )?\d|upgrade to (pro|max)|failed to authenticate|"
                    r"authentication failed|oauth session expired|not logged in")


def _quota_notice(out: str) -> bool:
    return len(out) < 400 and bool(_QUOTA.search(out))


def claude_chat(model: str, prompt: str, system: str | None = None,
                timeout: int = 1800) -> str:
    """Claude Code CLI in print mode. Runs on the user's Claude subscription.

    `claude -p` with no positional message reads the prompt from stdin, which is
    the only way a dossier-sized prompt gets through on Windows (32k argv cap).
    """
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("claude no está instalado; instalá Claude Code o usá AW_BACKEND=hyper")
    args = [exe, "-p", "--output-format", "text", "--safe-mode", "--tools", "",
            "--system-prompt", system or "Write only the requested text in the requested language.",
            "--model", CLAUDE_ALIAS.get(model, model)]
    proc = subprocess.run(args, input=prompt, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError(f"claude {model} no devolvió texto: "
                           f"{(proc.stderr or '')[:300]}")
    if _quota_notice(out):
        raise RuntimeError(f"claude {model} sin cuota: {out}")
    return out


# A 4xx that will never fix itself: wrong key, wrong model name, malformed body.
# Retrying one of these burns the full request timeout four times and still 404s.
_FATAL_STATUS = {400, 401, 402, 403, 404}


def _status(e: Exception) -> int:
    """HTTP status behind an openai exception, 0 if it is not an HTTP error."""
    code = getattr(e, "status_code", None)
    if code is None:
        code = getattr(getattr(e, "response", None), "status_code", None)
    return int(code) if isinstance(code, int) else 0


def _backoff(attempt: int, status: int) -> int:
    """Seconds to wait before the next attempt.

    429 and 5xx mean the upstream has no capacity right now, which on a free
    model resolves in minutes, not in the 2-8s the plain exponential ramp waited:
    a 503 used to eat the four attempts in one breath and kill the run.
    """
    if status == 429 or status >= 500:
        return min(120, 15 * 2 ** attempt)
    return 2 ** attempt * 2


def _read_stream(r: Any) -> tuple[str, int, str]:
    """Drain a streamed completion into (text, reasoning words, finish reason).

    Reasoning tokens are counted, never returned: they are the model's scratchpad
    and putting them in the article would be inventing prose nobody wrote. They
    are worth counting because a reasoning model that answers with nothing but
    scratchpad is a different failure from a provider that answers with nothing.
    """
    parts: list[str] = []
    scratch: list[str] = []
    finish = ""
    for chunk in r:
        if not chunk.choices:
            continue
        choice = chunk.choices[0]
        parts.append(getattr(choice.delta, "content", None) or "")
        scratch.append(getattr(choice.delta, "reasoning_content", None) or "")
        finish = choice.finish_reason or finish
    return "".join(parts).strip(), len("".join(scratch).split()), finish


def hyper_chat(model: str, prompt: str, system: str | None = None, *,
               temperature: float = 0.8, max_tokens: int | None = None,
               retries: int = 4, backend: str = "hyper") -> str:
    """Any OpenAI-compatible endpoint (hyper, zen), with backoff between attempts.

    The call is **streamed**, and that is not cosmetic. A non-streamed request
    holds one open socket with nothing on it until the whole completion is
    written, so a slow reasoning model outlives both the client timeout
    (``AW_TIMEOUT``, 300s) and zen's own gateway: measured 2026-08-23 on
    ``zen/x-preview-f-free`` with the 7k-character topic prompt, the plain call
    died at 207s with HTTP 503 while the streamed one ran 341s to completion —
    first token at 2s, never more than 2.1s between chunks. Streaming turns the
    timeout into a per-chunk one, which is the thing actually worth measuring.
    """
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs: dict[str, Any] = {"model": model, "messages": messages,
                              "temperature": temperature, "stream": True}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    last: Exception | None = None
    for attempt in range(retries):
        status = 0
        try:
            out, reasoning, finish = _read_stream(
                client(backend).chat.completions.create(**kwargs))
            if out and finish != "length":
                return out
            last = RuntimeError(f"respuesta vacía o truncada (fin={finish or '?'}, "
                                f"{reasoning:,} palabras de razonamiento)")
            if finish == "length" and kwargs.get("max_tokens"):
                kwargs["max_tokens"] *= 2
        except Exception as e:  # noqa: BLE001 - transient upstream errors are the norm
            last, status = e, _status(e)
            if isinstance(e, FileNotFoundError):
                # A missing local binary (npx for the oauth proxy) never heals
                # between attempts: the four retries used to burn on [WinError 2].
                raise RuntimeError(f"{backend} necesita un binario que no está: {e}") from e
            if status in _FATAL_STATUS:
                raise RuntimeError(f"{model} no existe, la clave no sirve o no hay "
                                   f"saldo en {backend} (HTTP {status}): {e}") from e
        if attempt < retries - 1:
            wait = _backoff(attempt, status)
            # `last` names the failure: «sin texto» covered a timeout, a refusal
            # and a model that spent its whole budget thinking, and those are
            # three different bugs.
            ui.log(f"[llm] {model}: {'HTTP %d' % status if status else last}"
                   f"; reintento {attempt + 2}/{retries} en {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"{model} falló tras {retries} intentos: {last}")


# Set by the wizard: an attended run gets to answer for a dead provider instead
# of watching the whole chain fall over. Worker threads never prompt — input()
# from one of those would interleave with the pipeline's own output.
INTERACTIVE = False


def resolve_choice(raw: str, options: list[str]) -> str:
    """Accept an option either by name or by its 1-based index. '' = no match.

    Lives here rather than in ``main`` because ``_recover`` needs it too, and the
    wizard and the recovery prompt must read a menu answer the same way.
    """
    if raw.isdigit() and 1 <= int(raw) <= len(options):
        return options[int(raw) - 1]
    return raw if raw in options else ""


def _recover() -> None:
    """Interactive recovery after every link of the chain failed: hold or change."""
    while True:
        raw = input("\n¿[e]sperar 30s y reintentar, [c]ambiar proveedor/modelo, "
                    "[a]bortar? ").strip().lower()
        if raw.startswith("e"):
            time.sleep(30)
            return
        if raw.startswith("a"):
            raise KeyboardInterrupt("abortado por el usuario")
        if raw.startswith("c"):
            provs = list(PROVIDERS)
            print("\nProveedores:")
            for i, k in enumerate(provs, 1):
                print(f"  {i}) {k:<9} {PROVIDERS[k]['label']}")
            prov = resolve_choice(input(f"Proveedor [{'|'.join(provs)}]: ").strip(), provs)
            while not prov:
                print(f"Inválido. Elegí 1-{len(provs)} o uno de {provs}.")
                prov = resolve_choice(input(f"Proveedor [{'|'.join(provs)}]: ").strip(), provs)
            # Lazy import: main imports llm, so a module-level import would be
            # circular. pick_pair prints the provider's live catalogue and asks
            # for PRO/FLASH exactly like the wizard does.
            pro, flash = __import__("main").pick_pair(prov)
            rest = [b for b in CHAIN[1:] if b != prov]
            configure([prov, *rest], pro, flash)
            print(f"\n→ {describe()}\n")
            return


# Seconds between «sigue corriendo» ticks while a model call holds the console.
# A single completion can take minutes and prints nothing, which is
# indistinguishable from a hang; this says who owns the silence and for how long.
HEARTBEAT = int(os.environ.get("AW_HEARTBEAT", "60"))

_beats: list[threading.Event] = []


def _stop_all_beats() -> None:
    # A daemon tick printing into a dying interpreter aborts shutdown with
    # «could not acquire lock for <stdout>»; every ticker is silenced at exit.
    for ev in _beats:
        ev.set()


atexit.register(_stop_all_beats)


def _heartbeat(label: str) -> threading.Event:
    stop = threading.Event()
    _beats.append(stop)

    def tick():
        # Ticks only while the call is genuinely still running: once the event
        # is set the loop must exit without printing, or completion spins the
        # counter in a tight loop. No tick limit: it used to stop at ten, and
        # opencode (900s per attempt, 1800s with the sibling retry) and claude
        # (1800s) both outlive that — the call went silent right when the wait
        # started looking like a hang.
        waited = 0
        while not stop.wait(HEARTBEAT):
            waited += HEARTBEAT
            try:
                ui.log(f"[llm] {label}: sigue corriendo ({waited}s)…")
            except Exception:  # noqa: BLE001 - a dying console must not raise
                return

    threading.Thread(target=tick, daemon=True).start()
    return stop


def chat(model: str, prompt: str, system: str | None = None, *,
         temperature: float = 0.8, max_tokens: int | None = None,
         retries: int = 4, fallback: bool = True) -> str:
    """One-shot completion, walking the provider chain until one answers."""
    errors: list[str] = []
    for i, backend in enumerate(CHAIN):
        if i and not fallback:
            break
        if not _serves(backend, model):
            continue
        target = _as(backend, model)
        try:
            ui.log(f"[llm] {model} → {backend}/{target} "
                   f"(prompt de {len(prompt.split()):,} palabras)…")
            started = time.time()
            beat = _heartbeat(target)
            try:
                if backend == "claude":
                    out = claude_chat(target, prompt, system)
                elif backend == "go":
                    out = opencode_chat(target, prompt, system)
                else:
                    out = hyper_chat(target, prompt, system, temperature=temperature,
                                     max_tokens=max_tokens, retries=retries,
                                     backend=backend)
            finally:
                beat.set()
            ui.log(f"[llm] {target} respondió en {time.time() - started:.0f}s "
                   f"({len(out.split())} palabras)")
            return out
        except Exception as e:  # noqa: BLE001 - that is what the next link is for
            errors.append(f"{backend}/{target}: {type(e).__name__}: {e}")
            if i + 1 < len(CHAIN):
                print(f"[llm] {backend} no responde para {target}; sigo por "
                      f"{CHAIN[i + 1]}")
    failure = RuntimeError(f"ningún proveedor respondió para {model} — "
                           + " | ".join(errors or ["cadena vacía"]))
    if INTERACTIVE and threading.current_thread() is threading.main_thread():
        # The caller asked for a role, not a literal id: if the recovery
        # repointed PRO/FLASH, the retry must chase the new ones instead of
        # handing the old name to a provider that has never heard of it
        # (opus is not in oauth's catalogue, so the new head skipped it).
        was_pro, was_flash = model == PRO, model == FLASH
        _recover()
        model = PRO if was_pro else FLASH if was_flash else model
        return chat(model, prompt, system, temperature=temperature,
                    max_tokens=max_tokens, retries=retries, fallback=fallback)
    raise failure


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def chat_json(model: str, prompt: str, system: str | None = None,
              **kw: Any) -> Any:
    """Completion parsed as JSON. Retries once with a repair nudge.

    Models wrap JSON in prose or fences often enough that a tolerant extractor
    beats strict parsing; the second pass only fires when extraction fails.
    """
    sys_msg = (system or "") + "\n\nResponde EXCLUSIVAMENTE con JSON válido, sin texto adicional."
    raw = chat(model, prompt, sys_msg.strip(), **kw)
    for candidate in _json_candidates(raw):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    repaired = chat(model, f"Convierte esto en JSON válido y nada más:\n\n{raw[:20000]}",
                    "Devuelve solo JSON.", temperature=0.0)
    for candidate in _json_candidates(repaired):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Could not parse JSON from {model}:\n{raw[:800]}")


def _json_candidates(raw: str):
    yield raw.strip()
    m = _FENCE.search(raw)
    if m:
        yield m.group(1).strip()
    for open_c, close_c in (("{", "}"), ("[", "]")):
        i, j = raw.find(open_c), raw.rfind(close_c)
        if i != -1 and j > i:
            yield raw[i:j + 1]
