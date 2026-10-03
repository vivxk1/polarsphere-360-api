"""Pluggable text generator for RAG.

Three backends, selected by LLM_BACKEND:
  local      - Qwen2.5-1.5B-Instruct via transformers, CPU only, no API key
  openai     - hosted model, needs OPENAI_API_KEY
  extractive - no generation at all; caller assembles the answer from passages

The local backend is the default so the stack works offline and costs nothing.
"""
from __future__ import annotations

import os
import threading
from typing import Optional

from .config import (
    LLM_BACKEND,
    LLM_MAX_NEW_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_THREADS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

_lock = threading.Lock()
_qwen = None


class Generator:
    name = "none"

    def available(self) -> bool:
        return False

    def generate(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class LocalQwenGenerator(Generator):
    name = "local"

    def __init__(self) -> None:
        global _qwen
        with _lock:
            if _qwen is None:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer

                # Measured on this CPU-only box: 4 threads ~6.8 tok/s, 16 ~1.0 tok/s.
                # More threads is actively worse for a 1.5B model at batch size 1.
                torch.set_num_threads(LLM_THREADS)
                tok = AutoTokenizer.from_pretrained(LLM_MODEL)
                model = AutoModelForCausalLM.from_pretrained(LLM_MODEL)
                model.eval()
                _qwen = (tok, model)
        self.tok, self.model = _qwen
        self.name = f"local:{LLM_MODEL}"

    def available(self) -> bool:
        return True

    def generate(self, system: str, user: str) -> str:
        import torch

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt, return_tensors="pt")
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=LLM_MAX_NEW_TOKENS,
                temperature=LLM_TEMPERATURE,
                do_sample=LLM_TEMPERATURE > 0,
                top_p=0.9,
                pad_token_id=self.tok.eos_token_id,
            )
        new_tokens = out[0][inputs["input_ids"].shape[-1]:]
        return self.tok.decode(new_tokens, skip_special_tokens=True).strip()


class OpenAIGenerator(Generator):
    name = "openai"

    def available(self) -> bool:
        return bool(OPENAI_API_KEY)

    def generate(self, system: str, user: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_NEW_TOKENS,
        )
        return (resp.choices[0].message.content or "").strip()


class ExtractiveGenerator(Generator):
    """No generation. Signals the RAG layer to assemble from retrieved passages."""

    name = "extractive"

    def available(self) -> bool:
        return True

    def generate(self, system: str, user: str) -> str:
        return ""


_gen: Optional[Generator] = None


def get_generator() -> Generator:
    global _gen
    if _gen is not None:
        return _gen
    backend = LLM_BACKEND.lower()
    if backend == "openai" and OPENAI_API_KEY:
        try:
            _gen = OpenAIGenerator()
            return _gen
        except Exception:
            pass
    if backend == "extractive":
        _gen = ExtractiveGenerator()
        return _gen
    try:
        _gen = LocalQwenGenerator()
    except Exception:
        _gen = ExtractiveGenerator()
    return _gen
