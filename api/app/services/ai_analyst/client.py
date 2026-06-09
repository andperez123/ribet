from __future__ import annotations

"""OpenAI client helpers for the AI analyst."""

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger("ribet.ai_analyst")


def call_openai_json(system: str, user: str, temperature: float = 0.3) -> tuple[dict[str, Any], dict[str, int] | None, str]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.openai_model
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    usage = None
    if resp.usage:
        usage = {
            "prompt_tokens": resp.usage.prompt_tokens or 0,
            "completion_tokens": resp.usage.completion_tokens or 0,
            "total_tokens": resp.usage.total_tokens or 0,
        }
    raw = resp.choices[0].message.content or "{}"
    return json.loads(raw), usage, model


def pack_to_json(pack) -> str:
    return json.dumps(pack.model_dump(mode="json"), indent=0)
