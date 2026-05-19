# 新能源股票 AI 研究终端提交说明

## 一、提交内容

本目录为可提交的软件交付包，包含：

- `app.py`：推荐启动入口，直接运行即可启动桌面端软件。
- `apps/api`：FastAPI 后端源码与测试。
- `apps/web`：Vue 3 + Vite + TypeScript 前端源码。
- `reports`：BYD 与 TSLA 示例研究报告附件。
- `README.md`：中文运行说明。
- `SUBMISSION_GUIDE.md`：本提交说明。
- `软件介绍与使用说明.docx`：Word 版软件介绍、安装启动和使用说明。

## 二、推荐启动方式

请在本目录打开 PowerShell，然后直接运行：

```powershell
python app.py
```

该方式是本交付包的推荐启动方式。`app.py` 会自动检查并安装缺失依赖，启动后端服务，构建并打开前端页面，最后进入桌面端研究终端。

如果电脑尚未安装 Node.js/npm 或 Python 环境不完整，请先安装对应运行环境。

## 三、开发模式

需要前端热更新调试时，可运行：

```powershell
python app.py --dev
```

普通演示、课程检查和提交验收建议使用：

```powershell
python app.py
```

## 四、首次启动流程

首次打开系统时，会先弹出基础资料设置窗口。用户需要填写：

- 显示名称
- 头像缩写
- 工作区名称
- 角色
- 简介，可选

保存后，系统会进入终端页面，并同步更新顶部头像、侧栏品牌和设置页个人资料。如果模型 API 尚未配置，系统会继续弹出模型 API 接入提醒；没有 API Key 时可选择演示模式。

## 五、功能说明

系统提供以下主要功能：

- 仪表盘：展示市场概览、候选池、AI 观察、行情走势和研究摘要。
- 基本面分析：提供财务数据、估值指标、DCF 模型、同业比较和风险提示。
- 新闻与情绪：汇总新闻事件、情绪趋势、主题标签和研究影响。
- 组合与对比：用于观察股票池、对比候选标的和辅助研究决策。
- 筛选与提醒：支持新能源股票候选筛选和研究提醒。
- AI 候选工作台：生成候选、查看候选详情、运行 AI 研究流程。
- 设置中心：维护个人资料、模型 API、界面偏好和本地配置。

## 六、报告附件

报告位于 `reports/` 目录：

- `BYD_002594_SZ.md`
- `BYD_002594_SZ.html`
- `BYD_002594_SZ.pdf`
- `TSLA.md`
- `TSLA.html`
- `TSLA.pdf`

报告内容为研究演示用途，包含免责声明，不构成投资建议。

## 七、验证命令

后端测试：

```powershell
cd apps/api
$env:PYTHONPATH=(Get-Location).Path
pytest tests
```

前端类型检查与构建：

```powershell
cd apps/web
npm run typecheck
npm run build
```

## 八、隐私与提交说明

交付包不应包含以下本地文件：

- `.runtime/`
- `node_modules/`
- `dist/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.env*`
- 本地 API Key
- 本地用户昵称、头像、浏览器缓存或 Qt WebEngine profile
- 开发烟测截图与运行日志

如果运行后产生上述目录或文件，请不要再次提交这些运行产物。
