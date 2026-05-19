# AGENTS.md

## Project

Build a broker-style AI equity research terminal for new-energy stocks. The MVP supports Tesla (`TSLA`) and BYD (`002594.SZ` / `01211.HK`).

## Rules

- Do not implement real-money trading.
- Do not provide personalized investment advice.
- Do not hallucinate financial numbers.
- Every generated report claim must be source-grounded or explicitly marked as an assumption.
- Prefer visible data-quality warnings over silent failures.
- Keep DCF assumptions visible and editable.
- Tests are required for financial formulas and report guardrails.
- Respect website terms of service and robots rules.
- Do not scrape paywalled or login-only data.

## Frontend

- Use Vue 3, TypeScript, Vite, Pinia, Naive UI, ECharts, and tokenized CSS.
- Default to the light broker style from the reference images; keep a dark terminal theme available.
- Keep tables dense, readable, and responsive.

## Backend

- Use FastAPI and Pydantic for API contracts.
- Keep provider adapters isolated behind service interfaces.
- Demo fixtures must remain available when live providers are not configured.

## AI

- Supervisor Agent coordinates specialized analysis agents.
- Report Writer Agent can only use validated intermediate outputs.
- Separate facts, calculations, assumptions, and caveats.

