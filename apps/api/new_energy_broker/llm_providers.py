from __future__ import annotations

from .schemas import LlmProtocol


def _preset(
    provider_id: str,
    name: str,
    region: str,
    protocol: LlmProtocol,
    base_url: str,
    default_model: str,
    api_key_hint: str,
    docs_url: str,
    notes: str,
) -> dict[str, str]:
    return {
        "id": provider_id,
        "name": name,
        "region": region,
        "protocol": protocol,
        "baseUrl": base_url,
        "defaultModel": default_model,
        "apiKeyHint": api_key_hint,
        "docsUrl": docs_url,
        "notes": notes,
    }


LLM_PROVIDER_PRESETS: list[dict[str, str]] = [
    _preset("openai", "OpenAI", "Global", "openai-compatible", "https://api.openai.com/v1", "gpt-4.1-mini", "OpenAI API key", "https://platform.openai.com/docs/api-reference", "OpenAI Chat Completions-compatible endpoint."),
    _preset("azure-openai", "Azure OpenAI", "Global", "azure-openai", "https://{resource}.openai.azure.com", "gpt-4.1-mini-deployment", "Azure OpenAI resource key", "https://learn.microsoft.com/azure/ai-foundry/openai/reference", "Use your Azure resource endpoint and deployment name as the model. API version is required."),
    _preset("anthropic", "Anthropic Claude", "Global", "anthropic-messages", "https://api.anthropic.com", "claude-3-5-sonnet-latest", "Anthropic API key", "https://docs.anthropic.com/en/api/messages", "Uses Anthropic Messages API with anthropic-version header."),
    _preset("google-gemini", "Google Gemini", "Global", "openai-compatible", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash", "Google AI Studio API key", "https://ai.google.dev/gemini-api/docs/openai", "Gemini OpenAI compatibility endpoint."),
    _preset("mistral", "Mistral AI", "Global", "openai-compatible", "https://api.mistral.ai/v1", "mistral-small-latest", "Mistral API key", "https://docs.mistral.ai/api/", "OpenAI-style chat completions endpoint."),
    _preset("xai", "xAI", "Global", "openai-compatible", "https://api.x.ai/v1", "grok-3-mini", "xAI API key", "https://docs.x.ai/docs/api-reference", "OpenAI-compatible xAI endpoint."),
    _preset("groq", "Groq", "Global", "openai-compatible", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "Groq API key", "https://console.groq.com/docs", "Groq OpenAI-compatible endpoint."),
    _preset("openrouter", "OpenRouter", "Global", "openai-compatible", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini", "OpenRouter API key", "https://openrouter.ai/docs/api-reference/overview", "Multi-provider OpenAI-like gateway."),
    _preset("together-ai", "Together AI", "Global", "openai-compatible", "https://api.together.xyz/v1", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "Together API key", "https://docs.together.ai/reference/chat-completions", "OpenAI-compatible chat completions endpoint."),
    _preset("deepseek", "DeepSeek", "China / Global", "openai-compatible", "https://api.deepseek.com", "deepseek-chat", "DeepSeek API key", "https://api-docs.deepseek.com/", "OpenAI-compatible endpoint."),
    _preset("qwen", "Qwen / Alibaba Model Studio", "China / International", "openai-compatible", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "DashScope API key", "https://www.alibabacloud.com/help/en/model-studio/use-qwen-by-calling-api", "For international/Singapore region use https://dashscope-intl.aliyuncs.com/compatible-mode/v1."),
    _preset("kimi", "Kimi / Moonshot", "China", "openai-compatible", "https://api.moonshot.cn/v1", "kimi-k2.6", "Moonshot API key", "https://platform.kimi.com/docs/api/overview", "OpenAI-compatible Kimi endpoint. Some tools also use https://api.moonshot.ai/v1."),
    _preset("zhipu-glm", "Zhipu GLM / Z.ai", "China", "openai-compatible", "https://open.bigmodel.cn/api/paas/v4", "glm-4.5-flash", "BigModel API key", "https://docs.bigmodel.cn/cn/guide/start/model-overview", "OpenAI-compatible GLM endpoint."),
    _preset("baidu-qianfan", "Baidu Qianfan", "China", "openai-compatible", "https://qianfan.baidubce.com/v2", "ernie-4.5-turbo-128k", "Baidu Qianfan API key", "https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html", "Qianfan v2 OpenAI-compatible endpoint."),
    _preset("tencent-hunyuan", "Tencent Hunyuan", "China", "openai-compatible", "https://api.hunyuan.cloud.tencent.com/v1", "hunyuan-turbos-latest", "Tencent Hunyuan API key", "https://cloud.tencent.com/document/product/1729", "Hunyuan OpenAI-compatible endpoint."),
    _preset("minimax", "MiniMax", "China / Global", "openai-compatible", "https://api.minimax.io/v1", "MiniMax-M2", "MiniMax API key", "https://platform.minimax.io/docs/api-reference/models/openai/list-models", "International endpoint. China users may use https://api.minimaxi.com/v1."),
    _preset("volcengine-ark", "Volcengine Ark / Doubao", "China", "openai-compatible", "https://ark.cn-beijing.volces.com/api/v3", "doubao-seed-1-6", "Volcengine Ark API key", "https://www.volcengine.com/docs/82379", "Ark OpenAI-compatible endpoint."),
    _preset("siliconflow", "SiliconFlow", "China / Global", "openai-compatible", "https://api.siliconflow.cn/v1", "Qwen/Qwen3-32B", "SiliconFlow API key", "https://docs.siliconflow.cn/", "OpenAI-compatible SiliconFlow endpoint."),
    _preset("custom", "Custom OpenAI-compatible", "Custom", "openai-compatible", "https://your-provider.example/v1", "your-model", "Provider API key", "", "Use any provider that supports OpenAI Chat Completions-compatible requests."),
]


def get_provider_preset(provider_id: str) -> dict[str, str]:
    normalized = provider_id.strip().lower()
    for preset in LLM_PROVIDER_PRESETS:
        if preset["id"] == normalized:
            return preset
    return LLM_PROVIDER_PRESETS[-1]
