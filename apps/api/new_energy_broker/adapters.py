from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .demo_data import FINANCIALS
from .schemas import FinancialRow
from .services import canonical_ticker


@dataclass(frozen=True)
class AdapterStatus:
    provider: str
    configured: bool
    mode: str
    message: str


class FinancialDataAdapter:
    provider = "base"

    def status(self) -> AdapterStatus:
        return AdapterStatus(provider=self.provider, configured=False, mode="demo", message="Base adapter")

    def load_financials(self, ticker: str) -> list[FinancialRow]:
        return FINANCIALS[canonical_ticker(ticker)]


class SecEdgarAdapter(FinancialDataAdapter):
    provider = "sec-edgar"

    def status(self) -> AdapterStatus:
        return AdapterStatus(
            provider=self.provider,
            configured=True,
            mode="hybrid",
            message="SEC/EDGAR hook is available; MVP returns curated financial rows unless live sync is enabled.",
        )


class ChinaFinancialAdapter(FinancialDataAdapter):
    provider = "china-akshare-tushare-csv"

    def __init__(self, csv_root: Path | None = None) -> None:
        self.csv_root = csv_root

    def status(self) -> AdapterStatus:
        csv_ready = bool(self.csv_root and self.csv_root.exists())
        return AdapterStatus(
            provider=self.provider,
            configured=csv_ready,
            mode="hybrid",
            message="AKShare/Tushare hooks are reserved; CSV fallback uses demo rows when no CSV is present.",
        )


def provider_statuses() -> list[AdapterStatus]:
    return [SecEdgarAdapter().status(), ChinaFinancialAdapter().status()]

