from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from .schemas import LlmConfig

Message = dict[str, str]


@dataclass(frozen=True)
class BuiltLlmRequest:
    full_url: str
    headers: dict[str, str]
    payload: dict[str, object]


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _openai_compatible_request(llm: LlmConfig, messages: list[Message], temperature: float) -> BuiltLlmRequest:
    return BuiltLlmRequest(
        full_url=_join_url(llm.base_url, "chat/completions"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {llm.api_key}"},
        payload={"model": llm.model, "temperature": temperature, "messages": messages},
    )


def _anthropic_messages_request(llm: LlmConfig, messages: list[Message], temperature: float) -> BuiltLlmRequest:
    system_parts = [item["content"] for item in messages if item.get("role") == "system"]
    conversation = [item for item in messages if item.get("role") != "system"]
    return BuiltLlmRequest(
        full_url=_join_url(llm.base_url, "v1/messages"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": llm.api_key,
            "anthropic-version": "2023-06-01",
        },
        payload={
            "model": llm.model,
            "max_tokens": 1200,
            "temperature": temperature,
            "system": "\n\n".join(system_parts),
            "messages": conversation,
        },
    )


def _azure_openai_request(llm: LlmConfig, messages: list[Message], temperature: float) -> BuiltLlmRequest:
    api_version = llm.api_version or "2025-01-01-preview"
    deployment = quote(llm.model, safe="")
    return BuiltLlmRequest(
        full_url=f"{llm.base_url.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={quote(api_version, safe='')}",
        headers={"Content-Type": "application/json", "api-key": llm.api_key},
        payload={"messages": messages, "temperature": temperature},
    )


def build_llm_request(llm: LlmConfig, messages: list[Message], temperature: float = 0.2) -> BuiltLlmRequest:
    if llm.protocol == "anthropic-messages":
        return _anthropic_messages_request(llm, messages, temperature)
    if llm.protocol == "azure-openai":
        return _azure_openai_request(llm, messages, temperature)
    return _openai_compatible_request(llm, messages, temperature)


def extract_llm_content(body: dict[str, object]) -> str:
    if "choices" in body:
        choices = body["choices"]
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
                if isinstance(first.get("text"), str):
                    return first["text"]
    content = body.get("content")
    if isinstance(content, list):
        return "".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") in {None, "text"} and isinstance(item.get("text"), str)
        )
    if isinstance(content, str):
        return content
    raise KeyError("No supported model content field found")
