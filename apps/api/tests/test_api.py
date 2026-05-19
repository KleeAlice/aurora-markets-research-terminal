from __future__ import annotations

from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient

from new_energy_broker import config_store
from new_energy_broker.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_security_alias_lookup():
    response = client.get("/api/securities/01211.HK")
    assert response.status_code == 200
    assert response.json()["ticker"] == "002594.SZ"


def test_dashboard_payload_for_byd():
    response = client.get("/api/dashboard/01211.HK")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "002594.SZ"
    assert payload["watchlist"]
    assert payload["heatmap"]
    assert payload["valuation_snapshot"]


def test_candles_are_valid_ohlcv_rows():
    response = client.get("/api/market/BYD/candles?range=1D")
    assert response.status_code == 200
    candles = response.json()
    assert len(candles) >= 50
    first = candles[0]
    assert first["high"] >= max(first["open"], first["close"])
    assert first["low"] <= min(first["open"], first["close"])
    assert first["volume"] >= 0


def test_analysis_job_creates_completed_report():
    response = client.post("/api/analysis/jobs", json={"ticker": "TSLA"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["created_report_id"]


def test_pdf_export_returns_pdf_content_type():
    response = client.get("/api/reports/TSLA/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_market_search_returns_source_status():
    response = client.get("/api/market/search?q=tesla")
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert "data_status" in payload[0]
    assert payload[0]["source"]["title"]


def test_stock_picker_suggestions_are_research_candidates():
    response = client.post(
        "/api/agent/stock-picker/suggestions",
        json={"theme": "new energy vehicles", "tickers": ["TSLA", "BYD"], "max_results": 3, "language": "en"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload
    joined = " ".join(item["thesis"].lower() for item in payload)
    assert "research candidate" in joined
    assert "buy" not in joined
    assert payload[0]["sources"]


def test_api_config_persists_to_runtime_file(tmp_path, monkeypatch):
    config_file = tmp_path / "model_api_settings.json"
    monkeypatch.setattr(config_store, "CONFIG_PATH", config_file)

    payload = {
        "provider": "OpenAI",
        "providerId": "openai",
        "protocol": "openai-compatible",
        "baseUrl": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
        "apiKey": "unit-test-key",
        "apiVersion": "",
        "marketDataProvider": "Demo fixtures",
        "marketDataKey": "",
        "configured": True,
        "demoMode": False,
        "savedAt": "",
    }
    response = client.put("/api/settings/api-config", json=payload)
    assert response.status_code == 200
    assert config_file.exists()

    restored = client.get("/api/settings/api-config")
    assert restored.status_code == 200
    data = restored.json()
    assert data["configured"] is True
    assert data["apiKey"] == "unit-test-key"
    assert data["protocol"] == "openai-compatible"
    assert data["savedAt"]


def test_llm_provider_presets_endpoint_lists_supported_vendors():
    response = client.get("/api/settings/llm-providers")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 19
    assert {item["id"] for item in payload} >= {"openai", "anthropic", "azure-openai", "deepseek", "qwen", "custom"}


def test_research_run_refreshes_dashboard_and_assets():
    response = client.post(
        "/api/agent/research-runs",
        json={"theme": "new energy vehicles", "tickers": ["TSLA", "BYD"], "max_results": 3, "primary_ticker": "TSLA", "language": "zh"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"queued", "running", "completed"}
    run_id = payload["id"]

    completed = payload
    for _ in range(80):
        sleep(0.25)
        completed = client.get(f"/api/agent/research-runs/{run_id}").json()
        if completed["status"] == "completed":
            break

    assert completed["status"] == "completed"
    assert completed["dashboard"]["selected_shortlist"]
    assert completed["dashboard"]["data_status"]["mode"] in {"delayed", "demo", "mixed"}
    assert completed["assets"]
    assert completed["steps"][-1]["status"] == "completed"
    assert "完成" in completed["message"]


def test_research_run_trace_is_ordered_and_chinese():
    response = client.post(
        "/api/agent/research-runs",
        json={"theme": "new energy vehicles", "tickers": ["TSLA", "BYD"], "max_results": 2, "language": "zh"},
    )
    assert response.status_code == 200
    run_id = response.json()["id"]

    for _ in range(80):
        sleep(0.25)
        run = client.get(f"/api/agent/research-runs/{run_id}").json()
        if run["status"] == "completed":
            break

    trace_response = client.get(f"/api/agent/research-runs/{run_id}/trace")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert trace
    assert [event["sequence"] for event in trace] == sorted(event["sequence"] for event in trace)
    phases = {event["phase"] for event in trace}
    assert {"检索", "行情", "排序", "图片", "面板", "研报"}.issubset(phases)
    assert any("搜索" in event["title"] or "检索" in event["title"] for event in trace)
    assert all(event["timestamp"] for event in trace)


def test_image_asset_endpoint_returns_content():
    run = client.post("/api/agent/research-runs", json={"tickers": ["TSLA"], "max_results": 1}).json()
    for _ in range(80):
        sleep(0.25)
        run = client.get(f"/api/agent/research-runs/{run['id']}").json()
        if run["status"] == "completed":
            break
    asset_id = run["assets"][0]["id"]
    response = client.get(f"/api/assets/images/{asset_id}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
