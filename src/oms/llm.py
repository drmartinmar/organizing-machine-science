"""LLM backends with a record/replay cache.

Backends implement ``complete(messages, schema=None, model=None, meta=None)`` and
return an ``LLMResponse``.  Three backends are provided:

* ``OpenAICompatibleBackend`` – any OpenAI-compatible chat endpoint (OpenAI,
  OpenRouter, vLLM, Ollama, LM Studio); configured by ``OMS_BASE_URL``,
  ``OMS_API_KEY`` (falls back to ``OPENAI_API_KEY``) and ``OMS_MODEL``.
* ``CodexBackend`` – drives the OpenAI Codex CLI (``codex exec``) as a plain
  completion engine with JSON-schema output.  Useful where API keys are not
  available but a Codex/ChatGPT login is.
* ``MockBackend`` – deterministic, key-free responses used for tests and CI.

``CachingBackend`` wraps any backend and records every (request, response)
pair in a JSONL cache keyed by a content hash.  With ``mode="replay"`` the
cache is the only source of responses, which makes a published experiment
exactly reproducible without model access.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict = field(default_factory=dict)
    cached: bool = False
    latency_s: float = 0.0

    def json(self) -> Any:
        return parse_json(self.text)


def parse_json(text: str) -> Any:
    """Parse JSON from a model reply, tolerating code fences and leading prose."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    s = s.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        start = min([i for i in (s.find("{"), s.find("[")) if i >= 0], default=-1)
        if start < 0:
            raise
        depth, in_str, esc = 0, False, False
        opener = s[start]
        closer = "}" if opener == "{" else "]"
        for i in range(start, len(s)):
            ch = s[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
                if depth == 0:
                    return json.loads(s[start:i + 1])
        raise


class Backend:
    name = "base"

    def complete(self, messages: list[dict], *, schema: dict | None = None, model: str | None = None,
                 temperature: float | None = None, meta: dict | None = None) -> LLMResponse:
        raise NotImplementedError


class OpenAICompatibleBackend(Backend):
    name = "openai"

    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None,
                 max_retries: int = 3):
        from openai import OpenAI  # lazy import
        self.model = model or os.environ.get("OMS_MODEL", "gpt-4.1")
        self.client = OpenAI(base_url=base_url or os.environ.get("OMS_BASE_URL") or None,
                             api_key=api_key or os.environ.get("OMS_API_KEY") or os.environ.get("OPENAI_API_KEY"))
        self.max_retries = max_retries

    def complete(self, messages, *, schema=None, model=None, temperature=None, meta=None) -> LLMResponse:
        kwargs: dict[str, Any] = {"model": model or self.model, "messages": messages}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if schema is not None:
            kwargs["response_format"] = {"type": "json_schema",
                                         "json_schema": {"name": "oms_output", "schema": schema, "strict": False}}
        t0 = time.time()
        last = None
        for attempt in range(self.max_retries):
            try:
                r = self.client.chat.completions.create(**kwargs)
                usage = {"prompt_tokens": r.usage.prompt_tokens, "completion_tokens": r.usage.completion_tokens} if r.usage else {}
                return LLMResponse(text=r.choices[0].message.content or "", model=r.model, usage=usage,
                                   latency_s=time.time() - t0)
            except Exception as e:  # pragma: no cover - network
                last = e
                time.sleep(2 ** attempt)
        raise RuntimeError(f"OpenAI-compatible call failed: {last}")


class CodexBackend(Backend):
    """Use ``codex exec`` as a stateless completion engine.

    The system and user messages are flattened into one prompt.  The model is
    told not to use tools; ``--output-schema`` enforces the JSON schema on the
    final message when one is given.
    """
    name = "codex"

    def __init__(self, model: str = "gpt-6-astra", reasoning_effort: str = "medium", timeout_s: int = 900,
                 max_retries: int = 2):
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    def complete(self, messages, *, schema=None, model=None, temperature=None, meta=None) -> LLMResponse:
        prompt_parts = []
        for m in messages:
            tag = m["role"].upper()
            prompt_parts.append(f"<{tag}>\n{m['content']}\n</{tag}>")
        prompt = ("You are being used as a plain language model. Do not run commands, read files or use any tools; "
                  "answer directly from the information in the messages below.\n\n" + "\n\n".join(prompt_parts))
        use_model = model or self.model
        t0 = time.time()
        last_err = None
        for attempt in range(self.max_retries + 1):
            with tempfile.TemporaryDirectory(prefix="oms-codex-") as td:
                out_path = Path(td) / "last.txt"
                cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only",
                       "-m", use_model, "-c", f'model_reasoning_effort="{self.reasoning_effort}"',
                       "-C", td, "-o", str(out_path)]
                if schema is not None:
                    sp = Path(td) / "schema.json"
                    sp.write_text(json.dumps(schema))
                    cmd += ["--output-schema", str(sp)]
                cmd.append("-")
                try:
                    proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=self.timeout_s)
                except subprocess.TimeoutExpired as e:
                    last_err = f"timeout after {self.timeout_s}s"
                    continue
                text = out_path.read_text() if out_path.exists() else ""
                if proc.returncode != 0 or not text.strip():
                    last_err = f"rc={proc.returncode} stderr={proc.stderr[-800:]}"
                    time.sleep(3 * (attempt + 1))
                    continue
                usage = _parse_codex_usage(proc.stderr + proc.stdout)
                return LLMResponse(text=text, model=use_model, usage=usage, latency_s=time.time() - t0)
        raise RuntimeError(f"codex exec failed: {last_err}")


def _parse_codex_usage(s: str) -> dict:
    import re
    m = re.search(r"tokens used\s*\n?\s*([\d,]+)", s)
    if m:
        return {"total_tokens": int(m.group(1).replace(",", ""))}
    return {}


class MockBackend(Backend):
    """Deterministic stand-in used by the test-suite and the ``mock`` backend.

    It produces schema-valid answers from the role tag and the world metadata
    that the collective passes in ``meta``.  It is *not* a model of anything:
    it restates the planted literature and the textbook consensus, which makes
    it a useful "parrot" reference point.
    """
    name = "mock"

    def complete(self, messages, *, schema=None, model=None, temperature=None, meta=None) -> LLMResponse:
        meta = meta or {}
        role = meta.get("role", "")
        spec = meta.get("spec")
        lit = meta.get("literature") or []
        payload: Any
        if role == "analyst_code":
            fo = spec.focal_outcome
            payload = {"code": (
                "import pandas as pd, statsmodels.formula.api as smf\n"
                "df = pd.read_csv('data.csv')\n"
                f"rhs = ' + '.join(c for c in df.columns if c not in ('unit_id', '{fo}'))\n"
                f"m = smf.ols('{fo} ~ ' + rhs, data=df).fit()\n"
                "print(m.summary().tables[1])\n"), "plan": "regress focal outcome on all covariates"}
        elif role in ("theorist", "solo", "synthesizer", "analyst_interpret", "subteam"):
            claims = []
            for i, l in enumerate(lit, start=1):
                c = dict(l["claim"])
                c.update({"id": f"C{i}", "confidence": 0.7, "basis": [f"literature:{l['id']}"],
                          "rationale": "Restates prior study.", "moderator": c.get("moderator"),
                          "interaction_sign": c.get("interaction_sign"), "mediator": c.get("mediator"),
                          "indirect_sign": c.get("indirect_sign"), "sign": c.get("sign")})
                claims.append(c)
            payload = {"theory_summary": "Mock theory restating the literature.", "claims": claims,
                       "limitations": "Mock output."}
            if role == "analyst_interpret":
                payload = {"findings": [{"claim_id": c["id"], "supported": True, "estimate": 0.2, "p_value": 0.01,
                                         "note": "mock"} for c in claims], "data_summary": "mock"}
        elif role == "critic":
            n = meta.get("n_claims", 0)
            payload = {"verdicts": [{"claim_id": f"C{i}", "verdict": "accept" if i % 3 else "reject",
                                     "reason": "mock"} for i in range(1, n + 1)], "concerns": "mock"}
        else:
            payload = {"ok": True}
        return LLMResponse(text=json.dumps(payload), model="mock", usage={}, latency_s=0.0)


class CachingBackend(Backend):
    """Record/replay wrapper. ``mode``: ``record`` (call through on miss) or ``replay`` (fail on miss)."""

    def __init__(self, inner: Backend | None, cache_path: Path, mode: str = "record"):
        self.inner = inner
        self.cache_path = Path(cache_path)
        self.mode = mode
        self.name = f"cache[{inner.name if inner else 'replay'}]"
        self._lock = threading.Lock()
        self._cache: dict[str, dict] = {}
        if self.cache_path.exists():
            for line in self.cache_path.read_text().splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self._cache[rec["key"]] = rec

    @staticmethod
    def key_for(messages, schema, model, temperature) -> str:
        blob = json.dumps({"messages": messages, "schema": schema, "model": model, "temperature": temperature},
                          sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()

    def complete(self, messages, *, schema=None, model=None, temperature=None, meta=None) -> LLMResponse:
        use_model = model or getattr(self.inner, "model", None)
        key = self.key_for(messages, schema, use_model, temperature)
        with self._lock:
            hit = self._cache.get(key)
        if hit is not None:
            return LLMResponse(text=hit["response"]["text"], model=hit["response"]["model"],
                               usage=hit["response"].get("usage", {}), cached=True)
        if self.mode == "replay" or self.inner is None:
            raise KeyError(f"replay cache miss for key {key[:12]}... (role={meta.get('role') if meta else None})")
        r = self.inner.complete(messages, schema=schema, model=model, temperature=temperature, meta=meta)
        rec = {"key": key, "model": use_model, "messages": messages, "schema": schema, "temperature": temperature,
               "response": {"text": r.text, "model": r.model, "usage": r.usage, "latency_s": round(r.latency_s, 2)},
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with self._lock:
            self._cache[key] = rec
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return r


def make_backend(name: str, *, model: str | None = None, cache_path: Path | None = None, mode: str = "record",
                 reasoning_effort: str = "medium") -> Backend:
    if name == "mock":
        inner: Backend | None = MockBackend()
    elif name == "codex":
        inner = CodexBackend(model=model or "gpt-6-astra", reasoning_effort=reasoning_effort)
    elif name == "openai":
        inner = OpenAICompatibleBackend(model=model)
    elif name == "replay":
        inner = None
        mode = "replay"
    else:
        raise ValueError(f"unknown backend {name}")
    if cache_path is not None:
        return CachingBackend(inner, cache_path, mode=mode)
    if inner is None:
        raise ValueError("replay backend needs a cache path")
    return inner
