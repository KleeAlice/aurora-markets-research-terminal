from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    sector: Mapped[str] = mapped_column(String(120), nullable=False)
    industry: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    securities: Mapped[list["SecurityListing"]] = relationship(back_populates="company")


class SecurityListing(Base):
    __tablename__ = "securities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    ticker: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    exchange: Mapped[str] = mapped_column(String(80))
    market: Mapped[str] = mapped_column(String(80))
    currency: Mapped[str] = mapped_column(String(16))
    primary_listing: Mapped[bool] = mapped_column(Boolean, default=True)
    company: Mapped[Company] = relationship(back_populates="securities")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(40), index=True)
    statement_type: Mapped[str] = mapped_column(String(40))
    period_type: Mapped[str] = mapped_column(String(20))
    fiscal_year: Mapped[int] = mapped_column(Integer)
    fiscal_period: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(16))
    line_item_code: Mapped[str] = mapped_column(String(120))
    line_item_name_original: Mapped[str] = mapped_column(String(240))
    line_item_name_standardized: Mapped[str] = mapped_column(String(160))
    value: Mapped[float] = mapped_column(Float)
    source_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisJobRecord(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(40), index=True)
    job_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40))
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_report_id: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(240))
    markdown: Mapped[str] = mapped_column(Text)
    html: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

