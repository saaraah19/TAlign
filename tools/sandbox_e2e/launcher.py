"""
DEV TOOL: runs the REAL Talign backend, but replaces the two AI providers
(which need Google's network and a key) with deterministic stand-ins, so the
whole app can be exercised end to end where Gemini is unreachable (a CI
sandbox, an offline machine). See README.md in this folder.

The stand-ins are crude on purpose: the "LLM" fills any requested schema with
placeholder values (so every score comes out 100) and the "embeddings" are
word-overlap hashes. They prove the PLUMBING works (routes, permissions,
database, background tasks, retrieval wiring), never the QUALITY of any AI
output. Never use this against real data.
"""

import hashlib
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from pydantic import ValidationError

import app.core.llm_provider as lp
from app.core.exceptions import InvalidStructuredOutputError
from app.models.knowledge_chunk import EMBEDDING_DIMENSION


def _gen(schema: dict, defs: dict):
    if "$ref" in schema:
        return _gen(defs[schema["$ref"].split("/")[-1]], defs)
    if "enum" in schema:
        for preferred in ("matched", "high", "strong"):
            if preferred in schema["enum"]:
                return preferred
        return schema["enum"][0]
    if "const" in schema:
        return schema["const"]
    if "anyOf" in schema:
        options = [o for o in schema["anyOf"] if o.get("type") != "null"]
        return _gen(options[0], defs) if options else None
    t = schema.get("type")
    if t == "string":
        text = "Sample text produced by the sandbox AI stand-in."
        return text.ljust(schema.get("minLength", 0), ".")
    if t == "integer":
        return (
            max(schema.get("minimum", 3), 3)
            if schema.get("maximum", 10**9) >= 3
            else schema.get("minimum", 0)
        )
    if t == "number":
        return (
            float(schema.get("minimum", 80.0))
            if schema.get("minimum", 0) > 80
            else min(80.0, float(schema.get("maximum", 80.0)))
        )
    if t == "boolean":
        return True
    if t == "array":
        n = max(1, schema.get("minItems", 1))
        return [_gen(schema.get("items", {}), defs) for _ in range(n)]
    if t == "object" or "properties" in schema:
        return {k: _gen(v, defs) for k, v in schema.get("properties", {}).items()}
    return None


class SandboxLLM(lp.LLMProvider):
    async def complete(self, messages, *, model=None, temperature=0.2):
        last = messages[-1].content[:60].replace("\n", " ")
        return lp.LLMResponse(
            content=f"[sandbox answer] Based on the stored context: {last}", model="sandbox-llm"
        )

    async def complete_structured(self, messages, *, response_schema, model=None, temperature=0.0):
        schema = response_schema.model_json_schema()
        data = _gen(schema, schema.get("$defs", {}))
        try:
            return response_schema.model_validate(data)
        except ValidationError as exc:  # surfaced as the app's real failure path
            raise InvalidStructuredOutputError(
                f"sandbox stand-in could not satisfy schema: {exc}"
            ) from exc


import re

_STOP = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "and",
    "or",
    "in",
    "on",
    "for",
    "is",
    "are",
    "do",
    "i",
    "my",
    "me",
    "we",
    "you",
    "it",
    "that",
    "this",
    "with",
    "as",
    "at",
    "by",
    "be",
    "can",
    "how",
    "what",
    "does",
    "get",
    "must",
}


class SandboxEmbeddings(lp.EmbeddingProvider):
    """Feature hashing: texts that share words get similar vectors (a crude stand-in for real semantics)."""

    def _vec(self, text):
        raw = [0.0] * EMBEDDING_DIMENSION
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            if word in _STOP:
                continue
            h = int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big")
            raw[h % EMBEDDING_DIMENSION] += 1.0
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    async def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    async def embed_query(self, text):
        return self._vec(text)

    @property
    def model_name(self):
        return "sandbox-embedding"

    @property
    def dimension(self):
        return EMBEDDING_DIMENSION


_llm, _emb = SandboxLLM(), SandboxEmbeddings()
lp.get_llm_provider = lambda: _llm
lp.get_embedding_provider = lambda: _emb

import uvicorn

uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
