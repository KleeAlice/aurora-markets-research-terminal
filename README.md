# Aurora Markets Research Terminal

新能源股票 AI 研究终端。

本项目是一个面向新能源股票研究的桌面端 AI 工作台，内置 BYD、TSLA 示例数据与报告，可用于演示股票基本面分析、候选筛选、新闻情绪、估值比较、AI 工作流和研究报告导出。

本软件仅用于课程设计、研究演示和辅助分析，不提供真实交易、开户注册、KYC、下单执行或个性化投资建议。

## 主要功能

- 仪表盘：查看市场概览、候选池、走势、AI 观察与研究摘要。
- 基本面分析：展示财务指标、DCF 估值、同业对比和关键风险。
- 新闻与情绪：汇总新闻事件、情绪趋势和关键主题。
- AI 候选工作台：生成候选股票，查看候选详情，并运行 AI 研究流程。
- 模型 API 接入：支持 OpenAI、Azure OpenAI、Anthropic、Gemini、DeepSeek、通义千问、Kimi、智谱、百度千帆、腾讯混元等主流厂商。
- 首次资料设置：首次进入时需要填写用户名、头像缩写、工作区名称和角色。
- 报告导出：内置 BYD 与 TSLA 示例报告，支持 Markdown、HTML、PDF 附件。

## 推荐启动方式

在本目录直接运行：

```powershell
python app.py
```

`app.py` 会自动完成以下工作：

- 检查并安装缺失的后端 Python 依赖。
- 检查并安装缺失的前端 npm 依赖。
- 构建并启动前端页面。
- 启动 FastAPI 后端服务。
- 打开 PySide6 桌面窗口；如果桌面 WebView 不可用，则自动使用默认浏览器打开。

首次启动会比较慢，因为需要安装依赖和构建前端。之后再次启动会明显更快。

## 开发模式启动

如果需要调试前端热更新，可以运行：

```powershell
python app.py --dev
```

开发模式会启动 Vite dev server，适合修改页面时使用；普通演示和提交检查建议使用 `python app.py`。

## 手动运行方式

如果希望分别启动后端和前端，也可以使用下面的命令。

后端：

```powershell
cd apps/api
python -m pip install -r requirements.txt
python -m uvicorn new_energy_broker.main:app --reload --port 8765
```

前端：

```powershell
cd apps/web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

然后打开：

```text
http://127.0.0.1:5173
```

## 首次使用

第一次打开应用时会先弹出基础资料设置窗口，需要填写：

- 显示名称
- 头像缩写
- 工作区名称
- 角色
- 简介，可选

保存后进入终端。如果尚未配置模型 API，系统会继续弹出模型 API 接入提醒；也可以选择演示模式先体验功能。

## 报告附件

示例报告位于 `reports/` 目录：

- `BYD_002594_SZ.md`
- `BYD_002594_SZ.html`
- `BYD_002594_SZ.pdf`
- `TSLA.md`
- `TSLA.html`
- `TSLA.pdf`

## 验证命令

后端测试：

```powershell
cd apps/api
$env:PYTHONPATH=(Get-Location).Path
pytest tests
```

前端检查：

```powershell
cd apps/web
npm run typecheck
npm run build
```
