from __future__ import annotations

from datetime import date

from .schemas import (
    CandlePoint,
    DashboardPayload,
    EventItem,
    FinancialRow,
    HeatmapItem,
    MarketPoint,
    NewsCard,
    PeerMetric,
    Security,
    SentimentPoint,
    SentimentSummary,
    SourceRef,
    ValuationSnapshot,
    WatchlistItem,
)


SEC = SourceRef(title="SEC company facts / filings", url="https://www.sec.gov/edgar", source_type="filing")
BYD_IR = SourceRef(title="BYD investor relations reports", url="https://www.bydglobal.com/en/Investor.html", source_type="company_report")
DEMO = SourceRef(title="Curated MVP demo fixture", url="local://demo-fixtures", source_type="demo")


SECURITIES = {
    "TSLA": Security(
        ticker="TSLA",
        aliases=["TSLA.US"],
        company_name="Tesla, Inc.",
        exchange="NASDAQ",
        market="United States",
        currency="USD",
        sector="Consumer Discretionary",
        industry="Electric Vehicles and Energy",
        latest_price=178.61,
        market_cap=571_800_000_000,
        latest_report_date=date(2024, 12, 31),
        data_update_status="demo",
        thesis_tags=["EV benchmark", "Energy storage", "Autonomy optionality"],
    ),
    "002594.SZ": Security(
        ticker="002594.SZ",
        aliases=["01211.HK", "BYD"],
        company_name="BYD Company Limited",
        exchange="SZSE",
        market="China",
        currency="CNY",
        sector="Consumer Discretionary",
        industry="New Energy Vehicles and Batteries",
        latest_price=238.60,
        market_cap=646_000_000_000,
        latest_report_date=date(2024, 12, 31),
        data_update_status="demo",
        thesis_tags=["Vertical integration", "Battery advantage", "Export expansion"],
    ),
}


MARKET_OVERVIEW = [
    MarketPoint(label="S&P 500", value=5303.27, change_pct=0.62, series=[5210, 5230, 5255, 5248, 5290, 5303]),
    MarketPoint(label="NASDAQ", value=16685.97, change_pct=0.84, series=[16410, 16480, 16520, 16510, 16600, 16685]),
    MarketPoint(label="Hang Seng", value=19578.09, change_pct=1.21, series=[19140, 19210, 19320, 19260, 19480, 19578]),
    MarketPoint(label="NIKKEI 225", value=39069.68, change_pct=-0.24, series=[39120, 39080, 39020, 39060, 38980, 39069]),
    MarketPoint(label="USD/CNY", value=7.2176, change_pct=-0.05, series=[7.22, 7.21, 7.23, 7.22, 7.218, 7.2176]),
    MarketPoint(label="Crude Oil (WTI)", value=78.36, change_pct=1.08, series=[76.8, 77.2, 77.4, 77.1, 78.0, 78.36]),
]


def _candles(start: float, count: int, seed: int) -> list[CandlePoint]:
    rows: list[CandlePoint] = []
    close = start
    for index in range(count):
        drift = ((index * 7 + seed) % 11 - 4) * 0.22
        if 18 < index < 28:
            drift -= 0.55
        if index > count * 0.58:
            drift += 0.48
        open_ = close + (((index + seed) % 5) - 2) * 0.18
        close = max(1, open_ + drift)
        high = max(open_, close) + 0.75 + ((index + seed) % 4) * 0.18
        low = min(open_, close) - 0.72 - ((index + seed) % 3) * 0.16
        rows.append(
            CandlePoint(
                timestamp=f"May {12 + index // 12} {9 + (index % 12):02d}:30",
                open=round(open_, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close, 2),
                volume=round(1_000_000 + ((index * 137 + seed * 97) % 900_000), 0),
            )
        )
    return rows


CANDLES = {
    "002594.SZ": {
        "1D": _candles(226.8, 64, 3),
        "5D": _candles(224.2, 72, 5),
        "1M": _candles(211.0, 84, 7),
        "3M": _candles(198.0, 90, 9),
        "6M": _candles(184.0, 96, 11),
        "YTD": _candles(176.0, 96, 13),
        "1Y": _candles(164.0, 100, 15),
        "5Y": _candles(88.0, 120, 17),
    },
    "TSLA": {
        "1D": _candles(176.2, 64, 21),
        "5D": _candles(171.0, 72, 23),
        "1M": _candles(164.0, 84, 25),
        "3M": _candles(188.0, 90, 27),
        "6M": _candles(214.0, 96, 29),
        "YTD": _candles(230.0, 96, 31),
        "1Y": _candles(252.0, 100, 33),
        "5Y": _candles(46.0, 120, 35),
    },
}


WATCHLIST = [
    WatchlistItem(ticker="BYD", company_name="BYD Company", exchange="1211.HK", price=238.60, change_pct=2.93, sparkline=[230, 231, 232, 233, 232, 235, 238]),
    WatchlistItem(ticker="CATL", company_name="Contemporary Amperex", exchange="300750.SZ", price=206.45, change_pct=1.75, sparkline=[200, 201, 202, 204, 203, 205, 206]),
    WatchlistItem(ticker="TSLA", company_name="Tesla, Inc.", exchange="NASDAQ", price=178.61, change_pct=-0.58, sparkline=[184, 182, 181, 179, 180, 178, 178.6]),
    WatchlistItem(ticker="NIO", company_name="NIO Inc.", exchange="NYSE", price=4.35, change_pct=1.64, sparkline=[4.1, 4.15, 4.2, 4.18, 4.28, 4.31, 4.35]),
]


HEATMAP = [
    HeatmapItem(ticker="TSLA", change_pct=0.62, weight=1.4),
    HeatmapItem(ticker="BYD", change_pct=2.93, weight=1.6),
    HeatmapItem(ticker="CATL", change_pct=1.75, weight=1.2),
    HeatmapItem(ticker="NIO", change_pct=1.64, weight=1.0),
    HeatmapItem(ticker="LI", change_pct=2.11, weight=1.0),
    HeatmapItem(ticker="XPEV", change_pct=-0.34, weight=0.9),
]


NEWS = [
    NewsCard(title="BYD launches new Seal 06 DM-i with AI-powered efficiency upgrade", source="Reuters", date=date(2024, 5, 17), category="Featured", summary="BYD unveils a plug-in hybrid product cycle update, supporting the mid-size PHEV segment.", image_key="byd"),
    NewsCard(title="CATL unveils next-gen sodium-ion battery", source="Bloomberg", date=date(2024, 5, 16), category="Industry", summary="Battery cost innovation remains a core theme for the new-energy chain.", image_key="battery"),
    NewsCard(title="Tesla cuts prices in Europe again", source="CNBC", date=date(2024, 5, 15), category="Earnings", summary="Investors continue to watch volume elasticity and margin pressure.", image_key="tesla"),
]


VALUATION_SNAPSHOT = [
    ValuationSnapshot(ticker="BYD", pe=20.1, ps=1.5, ev_ebitda=13.2),
    ValuationSnapshot(ticker="CATL", pe=18.7, ps=2.6, ev_ebitda=11.6),
    ValuationSnapshot(ticker="TSLA", pe=53.8, ps=7.1, ev_ebitda=32.4),
    ValuationSnapshot(ticker="NIO", pe=None, ps=1.2, ev_ebitda=None),
]


FINANCIALS = {
    "TSLA": [
        FinancialRow(fiscal_year=2019, revenue=24.58, net_income=-0.86, gross_margin=0.165, roe=-0.108, operating_cash_flow=2.41, capital_expenditure=1.33, free_cash_flow=1.08, currency="USD_B", source=SEC),
        FinancialRow(fiscal_year=2020, revenue=31.54, net_income=0.72, gross_margin=0.210, roe=0.041, operating_cash_flow=5.94, capital_expenditure=3.16, free_cash_flow=2.78, currency="USD_B", source=SEC),
        FinancialRow(fiscal_year=2021, revenue=53.82, net_income=5.52, gross_margin=0.252, roe=0.204, operating_cash_flow=11.50, capital_expenditure=6.48, free_cash_flow=5.02, currency="USD_B", source=SEC),
        FinancialRow(fiscal_year=2022, revenue=81.46, net_income=12.56, gross_margin=0.255, roe=0.286, operating_cash_flow=14.72, capital_expenditure=7.16, free_cash_flow=7.56, currency="USD_B", source=SEC),
        FinancialRow(fiscal_year=2023, revenue=96.77, net_income=15.00, gross_margin=0.176, roe=0.173, operating_cash_flow=13.26, capital_expenditure=8.90, free_cash_flow=4.36, currency="USD_B", source=SEC),
    ],
    "002594.SZ": [
        FinancialRow(fiscal_year=2019, revenue=127.7, net_income=1.61, gross_margin=0.164, roe=0.028, operating_cash_flow=14.74, capital_expenditure=5.62, free_cash_flow=9.12, currency="CNY_B", source=BYD_IR),
        FinancialRow(fiscal_year=2020, revenue=156.6, net_income=4.23, gross_margin=0.193, roe=0.072, operating_cash_flow=45.39, capital_expenditure=21.20, free_cash_flow=24.19, currency="CNY_B", source=BYD_IR),
        FinancialRow(fiscal_year=2021, revenue=216.1, net_income=3.05, gross_margin=0.130, roe=0.043, operating_cash_flow=65.47, capital_expenditure=44.61, free_cash_flow=20.86, currency="CNY_B", source=BYD_IR),
        FinancialRow(fiscal_year=2022, revenue=424.1, net_income=16.62, gross_margin=0.174, roe=0.169, operating_cash_flow=140.84, capital_expenditure=101.20, free_cash_flow=39.64, currency="CNY_B", source=BYD_IR),
        FinancialRow(fiscal_year=2023, revenue=602.3, net_income=30.04, gross_margin=0.213, roe=0.201, operating_cash_flow=169.73, capital_expenditure=141.30, free_cash_flow=28.43, currency="CNY_B", source=BYD_IR),
    ],
}


PEERS = {
    "TSLA": [
        PeerMetric(ticker="002594.SZ", company_name="BYD", reason="Global EV benchmark", pe=23.2, ps=1.5, pb=4.6, ev_ebitda=13.7, revenue_growth=0.42, gross_margin=0.213, net_margin=0.050, roe=0.201, fcf_margin=0.047),
        PeerMetric(ticker="RIVN", company_name="Rivian", reason="US EV peer", pe=None, ps=2.1, pb=2.8, ev_ebitda=None, revenue_growth=1.67, gross_margin=-0.36, net_margin=-0.78, roe=-0.45, fcf_margin=-0.63),
        PeerMetric(ticker="LCID", company_name="Lucid", reason="US EV peer", pe=None, ps=5.2, pb=1.9, ev_ebitda=None, revenue_growth=0.13, gross_margin=-1.21, net_margin=-4.4, roe=-0.52, fcf_margin=-2.8),
        PeerMetric(ticker="F", company_name="Ford", reason="Traditional auto peer", pe=11.4, ps=0.32, pb=1.1, ev_ebitda=9.1, revenue_growth=0.11, gross_margin=0.095, net_margin=0.025, roe=0.102, fcf_margin=0.031),
        PeerMetric(ticker="GM", company_name="General Motors", reason="Traditional auto peer", pe=6.2, ps=0.36, pb=0.85, ev_ebitda=7.4, revenue_growth=0.10, gross_margin=0.117, net_margin=0.061, roe=0.151, fcf_margin=0.033),
    ],
    "002594.SZ": [
        PeerMetric(ticker="TSLA", company_name="Tesla", reason="Global EV benchmark", pe=37.6, ps=7.1, pb=9.5, ev_ebitda=26.2, revenue_growth=0.188, gross_margin=0.176, net_margin=0.155, roe=0.173, fcf_margin=0.045),
        PeerMetric(ticker="300750.SZ", company_name="CATL", reason="Battery-chain comparison", pe=18.7, ps=2.6, pb=4.2, ev_ebitda=11.6, revenue_growth=0.326, gross_margin=0.226, net_margin=0.112, roe=0.176, fcf_margin=0.084),
        PeerMetric(ticker="LI", company_name="Li Auto", reason="China EV peer", pe=22.6, ps=1.9, pb=3.6, ev_ebitda=14.2, revenue_growth=0.207, gross_margin=0.216, net_margin=0.087, roe=0.161, fcf_margin=0.095),
        PeerMetric(ticker="NIO", company_name="NIO", reason="China EV peer", pe=None, ps=1.2, pb=2.0, ev_ebitda=None, revenue_growth=0.214, gross_margin=0.102, net_margin=-0.38, roe=-0.086, fcf_margin=-0.23),
        PeerMetric(ticker="XPEV", company_name="XPeng", reason="China EV peer", pe=None, ps=1.4, pb=1.7, ev_ebitda=None, revenue_growth=0.182, gross_margin=0.061, net_margin=-0.42, roe=-0.124, fcf_margin=-0.31),
    ],
}


EVENTS = {
    "TSLA": [
        EventItem(event_title="Price cuts increase margin scrutiny", event_date=date(2024, 5, 15), source=DEMO, event_type="price_policy", summary="Recent market commentary focused on vehicle price reductions and their effect on automotive gross margin.", financial_impact="Possible near-term pressure on gross margin if volume elasticity is insufficient.", valuation_impact="Raises sensitivity to operating-margin assumptions in DCF.", risk_level="medium", opportunity_level="medium", affected_metrics=["gross_margin", "revenue_growth"], confidence=0.72),
        EventItem(event_title="Energy storage growth remains a positive narrative", event_date=date(2024, 5, 17), source=DEMO, event_type="product_growth", summary="Energy storage deployments continue to be discussed as a diversification driver.", financial_impact="Could support revenue mix if growth is sustained.", valuation_impact="Supports bull-case optionality, but evidence should be refreshed with filings.", risk_level="low", opportunity_level="high", affected_metrics=["revenue", "operating_margin"], confidence=0.68),
    ],
    "002594.SZ": [
        EventItem(event_title="BYD Seal product cycle highlights PHEV demand", event_date=date(2024, 5, 17), source=DEMO, event_type="product_launch", summary="New product launches strengthen the market narrative around plug-in hybrid demand and vertical integration.", financial_impact="May support sales volume and manufacturing utilization.", valuation_impact="Positive for growth assumptions if margins remain resilient.", risk_level="low", opportunity_level="high", affected_metrics=["revenue_growth", "gross_margin"], confidence=0.78),
        EventItem(event_title="Overseas expansion faces policy and tariff watchpoints", event_date=date(2024, 5, 19), source=DEMO, event_type="policy", summary="Global export expansion is strategically important but exposed to tariff and local-content rules.", financial_impact="Could add compliance costs or alter regional mix.", valuation_impact="Requires scenario treatment rather than single-point certainty.", risk_level="medium", opportunity_level="medium", affected_metrics=["revenue_growth", "tax_rate"], confidence=0.70),
    ],
}


SENTIMENT = {
    "TSLA": SentimentSummary(
        ticker="TSLA",
        label="neutral",
        score=0.18,
        confidence=0.66,
        source_breakdown={"news": 9, "filing": 2, "forum": 14},
        topic_clusters=["Delivery growth", "Gross margin pressure", "FSD", "Energy storage", "China competition"],
        expectation_gap="Market discussion gives high weight to autonomy optionality, while near-term fundamentals remain sensitive to pricing and margin delivery.",
        trend=[
            SentimentPoint(date=date(2024, 5, 12), positive=0.48, neutral=0.35, negative=0.17),
            SentimentPoint(date=date(2024, 5, 13), positive=0.51, neutral=0.33, negative=0.16),
            SentimentPoint(date=date(2024, 5, 14), positive=0.46, neutral=0.34, negative=0.20),
            SentimentPoint(date=date(2024, 5, 15), positive=0.42, neutral=0.37, negative=0.21),
            SentimentPoint(date=date(2024, 5, 16), positive=0.47, neutral=0.36, negative=0.17),
        ],
    ),
    "002594.SZ": SentimentSummary(
        ticker="002594.SZ",
        label="positive",
        score=0.57,
        confidence=0.74,
        source_breakdown={"news": 12, "company_report": 3, "forum": 21},
        topic_clusters=["Battery", "EV demand", "Price cuts", "Overseas expansion", "Subsidy policy"],
        expectation_gap="Narrative is constructive on volume and export growth; the main gap is whether margin resilience can match growth expectations.",
        trend=[
            SentimentPoint(date=date(2024, 5, 12), positive=0.63, neutral=0.19, negative=0.18),
            SentimentPoint(date=date(2024, 5, 13), positive=0.70, neutral=0.18, negative=0.12),
            SentimentPoint(date=date(2024, 5, 14), positive=0.68, neutral=0.22, negative=0.10),
            SentimentPoint(date=date(2024, 5, 15), positive=0.82, neutral=0.11, negative=0.07),
            SentimentPoint(date=date(2024, 5, 16), positive=0.73, neutral=0.16, negative=0.11),
            SentimentPoint(date=date(2024, 5, 17), positive=0.83, neutral=0.10, negative=0.07),
            SentimentPoint(date=date(2024, 5, 18), positive=0.67, neutral=0.21, negative=0.12),
            SentimentPoint(date=date(2024, 5, 19), positive=0.79, neutral=0.11, negative=0.10),
        ],
    ),
}
