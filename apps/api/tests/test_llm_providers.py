from __future__ import annotations

import json

from new_energy_broker.llm_providers import LLM_PROVIDER_PRESETS, get_provider_preset
from new_energy_broker.llm_client import build_llm_request, extract_llm_content
from new_energy_broker.schemas import LlmConfig


def test_provider_catalog_includes_mainstream_domestic_and_global_vendors():
    provider_ids = {item["id"] for item in LLM_PROVIDER_PRESETS}

    assert len(LLM_PROVIDER_PRESETS) >= 19
    assert {
        "openai",
        "azure-openai",
        "anthropic",
        "google-gemini",
        "mistral",
        "xai",
        "groq",
        "openrouter",
        "together-ai",
        "deepseek",
        "qwen",
        "kimi",
        "zhipu-glm",
        "baidu-qianfan",
        "tencent-hunyuan",
        "minimax",
        "volcengine-ark",
        "siliconflow",
        "custom",
    }.issubset(provider_ids)
    assert get_provider_preset("anthropic")["protocol"] == "anthropic-messages"
    assert get_provider_preset("azure-openai")["protocol"] == "azure-openai"
    assert get_provider_preset("deepseek")["baseUrl"] == "https://api.deepseek.com"


def test_openai_compatible_request_uses_chat_completions_and_bearer_auth():
    request = build_llm_request(
        LlmConfig(
            provider="DeepSeek",
            provider_id="deepseek",
            protocol="openai-compatible",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            api_key="unit-test-key",
        ),
        messages=[{"role": "user", "content": "rank candidates"}],
        temperature=0.2,
    )

    assert request.full_url == "https://api.deepseek.com/chat/completions"
    assert request.headers["Authorization"] == "Bearer unit-test-key"
    assert request.payload["model"] == "deepseek-chat"
    assert request.payload["messages"][0]["content"] == "rank candidates"


def test_anthropic_request_uses_messages_api_and_version_header():
    request = build_llm_request(
        LlmConfig(
            provider="Anthropic",
            provider_id="anthropic",
            protocol="anthropic-messages",
            base_url="https://api.anthropic.com",
            model="claude-3-5-sonnet-latest",
            api_key="anthropic-unit-test-key",
        ),
        messages=[
            {"role": "system", "content": "You rank only."},
            {"role": "user", "content": "rank candidates"},
        ],
        temperature=0.1,
    )

    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.headers["x-api-key"] == "anthropic-unit-test-key"
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert request.payload["system"] == "You rank only."
    assert request.payload["messages"] == [{"role": "user", "content": "rank candidates"}]
    assert request.payload["max_tokens"] > 0


def test_azure_openai_request_uses_deployment_url_api_version_and_api_key_header():
    request = build_llm_request(
        LlmConfig(
            provider="Azure OpenAI",
            provider_id="azure-openai",
            protocol="azure-openai",
            base_url="https://example-resource.openai.azure.com",
            model="gpt-4.1-mini-deployment",
            api_key="azure-test",
            api_version="2025-01-01-preview",
        ),
        messages=[{"role": "user", "content": "rank candidates"}],
        temperature=0.3,
    )

    assert request.full_url == "https://example-resource.openai.azure.com/openai/deployments/gpt-4.1-mini-deployment/chat/completions?api-version=2025-01-01-preview"
    assert request.headers["api-key"] == "azure-test"
    assert "Authorization" not in request.headers
    assert request.payload["messages"][0]["content"] == "rank candidates"


def test_extract_llm_content_supports_openai_and_anthropic_shapes():
    assert (
        extract_llm_content({"choices": [{"message": {"content": "{\"items\": []}"}}]})
        == "{\"items\": []}"
    )
    assert (
        extract_llm_content({"content": [{"type": "text", "text": json.dumps({"items": []})}]})
        == "{\"items\": []}"
    )
