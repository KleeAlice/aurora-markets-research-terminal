from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from .demo_data import CANDLES, SECURITIES
from .schemas import CandlePoint, MarketSearchResult, Security, SourceRef

YAHOO = SourceRef(title="Yahoo Finance delayed market data", url="https://finance.yahoo.com", source_type="market_data")
DEMO = SourceRef(title="Curated Aurora demo fallback", url="local://demo-fixtures", source_type="demo")

NEW_ENERGY_UNIVERSE = [
    ("TSLA", "Tesla, Inc.", "NASDAQ", "United States", "USD"),
    ("002594.SZ", "BYD Company Limited", "SZSE", "China", "CNY"),
    ("1211.HK", "BYD Company Limited", "HKEX", "Hong Kong", "HKD"),
    ("300750.SZ", "Contemporary Amperex Technology", "SZSE", "China", "CNY"),
    ("NIO", "NIO Inc.", "NYSE", "United States", "USD"),
    ("LI", "Li Auto Inc.", "NASDAQ", "United States", "USD"),
    ("XPEV", "XPeng Inc.", "NYSE", "United States", "USD"),
    ("RIVN", "Rivian Automotive, Inc.", "NASDAQ", "United States", "USD"),
    ("FSLR", "First Solar, Inc.", "NASDAQ", "United States", "USD"),
    ("ENPH", "Enphase Energy, Inc.", "NASDAQ", "United States", "USD"),
]


def _demo_market_data_mode() -> bool:
    return os.environ.get("AURORA_MARKET_DATA_MODE", "").strip().lower() in {"demo", "offline", "disabled"}


def canonical_ticker(ticker: str) -> str:
    value = ticker.upper()
    if value in {"BYD", "01211.HK", "1211.HK"}:
        return "002594.SZ"
    if value in {"TSLA.US"}:
        return "TSLA"
    return value


def _fetch_json(url: str, timeout: float = 5.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "AuroraMarketsResearchAgent/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def search_market(query: str) -> list[MarketSearchResult]:
    needle = query.strip().lower()
    local = [
        MarketSearchResult(
            ticker=ticker,
            company_name=name,
            exchange=exchange,
            market=market,
            currency=currency,
            data_status="demo",
            source=DEMO,
        )
        for ticker, name, exchange, market, currency in NEW_ENERGY_UNIVERSE
        if not needle or needle in ticker.lower() or needle in name.lower() or needle in market.lower()
    ]
    if _demo_market_data_mode():
        return local[:12]
    if needle:
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}&quotesCount=8&newsCount=0"
            payload = _fetch_json(url)
            remote: list[MarketSearchResult] = []
            for quote in payload.get("quotes", []):
                symbol = quote.get("symbol")
                name = quote.get("shortname") or quote.get("longname") or symbol
                if not symbol or quote.get("quoteType") not in {None, "EQUITY", "ETF"}:
                    continue
                remote.append(
                    MarketSearchResult(
                        ticker=symbol,
                        company_name=name,
                        exchange=quote.get("exchange", ""),
                        market=quote.get("market", ""),
                        currency="",
                        data_status="delayed",
                        source=YAHOO,
                    )
                )
            seen = set()
            combined = []
            for item in remote + local:
                if item.ticker not in seen:
                    seen.add(item.ticker)
                    combined.append(item)
            return combined[:12]
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return local[:12]
    return local[:12]


def delayed_quote(ticker: str) -> tuple[Security, SourceRef, str]:
    key = canonical_ticker(ticker)
    base = SECURITIES.get(key) or SECURITIES.get("TSLA")
    if base is None:
        raise KeyError(ticker)
    if _demo_market_data_mode():
        return base, DEMO, "Demo market-data mode enabled; using curated fallback quote."
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?range=1d&interval=1m"
        payload = _fetch_json(url)
        result = payload["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        previous = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        change_pct = None if not price or not previous else (price - previous) / abs(previous) * 100
        security = base.model_copy(
            update={
                "ticker": key,
                "latest_price": price or base.latest_price,
                "market_cap": meta.get("marketCap") or base.market_cap,
                "currency": meta.get("currency") or base.currency,
                "data_update_status": "delayed",
            }
        )
        return security, YAHOO, f"Delayed quote refreshed; day change {change_pct:.2f}%." if change_pct is not None else "Delayed quote refreshed."
    except (KeyError, IndexError, TypeError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return base, DEMO, "Real provider unavailable; using curated fallback quote."


def delayed_candles(ticker: str, range_key: str) -> tuple[list[CandlePoint], SourceRef, str]:
    key = canonical_ticker(ticker)
    yahoo_range = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "5Y": "5y"}.get(range_key.upper(), "1mo")
    interval = "5m" if yahoo_range in {"1d", "5d"} else "1d"
    if _demo_market_data_mode():
        ranges = CANDLES[key]
        return ranges.get(range_key.upper(), ranges["1D"]), DEMO, "Demo market-data mode enabled; using curated fallback OHLCV."
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?range={yahoo_range}&interval={interval}"
        payload = _fetch_json(url)
        result = payload["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        timestamps = result["timestamp"]
        rows: list[CandlePoint] = []
        for index, ts in enumerate(timestamps):
            open_ = quote["open"][index]
            high = quote["high"][index]
            low = quote["low"][index]
            close = quote["close"][index]
            volume = quote["volume"][index] or 0
            if None in {open_, high, low, close}:
                continue
            rows.append(
                CandlePoint(
                    timestamp=datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                    open=round(float(open_), 2),
                    high=round(float(high), 2),
                    low=round(float(low), 2),
                    close=round(float(close), 2),
                    volume=float(volume),
                )
            )
        if len(rows) >= 50:
            return rows[-160:], YAHOO, "Delayed OHLCV data refreshed."
    except (KeyError, IndexError, TypeError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        pass
    ranges = CANDLES[key]
    return ranges.get(range_key.upper(), ranges["1D"]), DEMO, "Real candle provider unavailable; using curated fallback OHLCV."
