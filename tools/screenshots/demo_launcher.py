"""
Runs the real Talign backend with the DEMO AI stand-in (demo_ai.py) instead of Gemini.
Used to produce the README screenshots. See README.md in this folder.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import app.core.llm_provider as lp
import demo_ai
import uvicorn

_llm, _emb = demo_ai.DemoLLM(), demo_ai.DemoEmbeddings()
lp.get_llm_provider = lambda: _llm
lp.get_embedding_provider = lambda: _emb

uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
