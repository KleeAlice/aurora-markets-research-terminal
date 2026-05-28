# Aurora Markets Research Terminal

AI equity research terminal for new-energy stocks, combining market research views, LLM-assisted workflows, and report export.

新能源股票 AI 研究终端。项目面向课程设计、研究演示和产品原型展示，内置 BYD、TSLA 示例数据与报告，可用于演示股票基本面分析、候选筛选、新闻情绪、估值比较、AI 工作流和研究报告导出。

> This project is for coursework, research demos, and assisted analysis only. It does not provide real trading, account opening, KYC, order execution, or personalized investment advice.

## Highlights

- Market dashboard for overview metrics, candidate pools, trends, AI observations, and research summaries.
- Fundamental analysis views for financial metrics, DCF valuation, peer comparison, and risk factors.
- News and sentiment workspace for event aggregation, sentiment trends, and topic exploration.
- AI candidate workbench for stock screening, candidate detail review, and AI research workflows.
- Multi-provider LLM configuration for OpenAI, Azure OpenAI, Anthropic, Gemini, DeepSeek, Qwen, Kimi, Zhipu, Baidu Qianfan, Tencent Hunyuan, and more.
- Built-in demo reports for BYD and TSLA with Markdown, HTML, and PDF attachments.

## Tech Stack

- Frontend: React, TypeScript, Vite
- Backend: Python, FastAPI
- Desktop shell: PySide6 WebView with browser fallback
- AI integration: configurable LLM provider adapters
- Reports: Markdown, HTML, PDF assets

## Recommended Start

Run from the project root:

```powershell
python app.py
```

`app.py` will:

- check and install missing Python backend dependencies;
- check and install missing frontend npm dependencies;
- build and start the frontend;
- start the FastAPI backend service;
- open the PySide6 desktop window, or fall back to the default browser when WebView is unavailable.

The first launch may take longer because dependencies and frontend assets need to be prepared. Later launches should be faster.

## Development Mode

For frontend hot reload:

```powershell
python app.py --dev
```

Development mode starts the Vite dev server. For demos and submission checks, use `python app.py`.

## Manual Start

Backend:

```powershell
cd apps/api
python -m pip install -r requirements.txt
python -m uvicorn new_energy_broker.main:app --reload --port 8765
```

Frontend:

```powershell
cd apps/web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

## First Use

On first launch, the app asks for basic profile information:

- display name;
- avatar initials;
- workspace name;
- role;
- optional short bio.

After saving, the terminal opens. If no model API is configured, the app shows an LLM provider setup reminder. Demo mode can be used first.

## Report Attachments

Example reports are stored in `reports/`:

- `BYD_002594_SZ.md`
- `BYD_002594_SZ.html`
- `BYD_002594_SZ.pdf`
- `TSLA.md`
- `TSLA.html`
- `TSLA.pdf`

## Verification

Backend tests:

```powershell
cd apps/api
$env:PYTHONPATH=(Get-Location).Path
pytest tests
```

Frontend checks:

```powershell
cd apps/web
npm run typecheck
npm run build
```
