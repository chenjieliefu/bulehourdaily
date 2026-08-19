# 微蓝日报（bulehourdaily）

每天把海外最新 AI 动态，转化成三个适合抖音发布的选题。

当前进度：**第 1 阶段（信息源与采集）** ✅、**第 2 阶段（热点事件 + 通用日报生成）** ✅ 已完成。

> 第 2 阶段起使用 DeepSeek；无 Key 时自动进入 mock 模式（界面可验收），真实验收前在 `.env` 配置 `MODEL_API_KEY`。

## 目录结构

```text
├── PRD.md                    # 产品需求文档
├── CONTEXT.md                # 领域术语表
├── 决策备忘.md               # 与产品经理确认过的关键决策
├── docs/
│   ├── 技术适配声明.md        # 技术选型结论
│   ├── 阶段1-技术开发文档.md  # 第 1 阶段详细方案
│   ├── 阶段2-技术开发文档.md  # 第 2 阶段详细方案
│   └── adr/                  # 架构决策记录
└── backend/                  # 后端代码
    ├── app/
    │   ├── api/              # API 路由
    │   ├── core/             # 配置、数据库、种子源
    │   ├── models/           # 数据表
    │   ├── schemas/          # 接口结构
    │   ├── services/         # 采集、去重、事件提取、日报生成、LLM
    │   │   └── prompts/      # Prompt 模板
    │   └── static/           # 验收界面（信息源/事件/日报 三页）
    ├── tests/                # 自动测试
    ├── alembic/              # 数据库迁移
    └── requirements.txt
```

## 环境要求

- Python 3.11（已装 3.11.9）
- DeepSeek API Key（可选；无 Key 时 mock 模式，真实验收前配置 `MODEL_API_KEY`）

## 启动步骤

```bash
cd backend

# 1. 创建虚拟环境（首次）
python3.11 -m venv .venv

# 2. 安装依赖（首次）
./.venv/bin/pip install -r requirements.txt

# 3. 初始化数据库（首次；已有 data/weilan.db 可跳过）
./.venv/bin/alembic upgrade head

# 4. 启动服务
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开浏览器访问 <http://127.0.0.1:8000/> 进入验收界面。

## 测试

```bash
cd backend
./.venv/bin/python -m pytest -q
```

## API 一览（前缀 /api/v1）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /sources | 信息源列表 |
| POST | /sources | 新增信息源 |
| PATCH | /sources/{id} | 修改信息源 |
| DELETE | /sources/{id} | 软停用 |
| POST | /collect/run | 手动触发采集 |
| GET | /source-items | 来源条目列表 |
| GET | /status | 采集状态 |
| POST | /events/extract | 触发事件提取（提交+轮询） |
| GET | /events | 热点事件列表 |
| GET | /events/{id} | 事件详情（含证据） |
| POST | /reports/generate | 生成日报（提交+轮询） |
| GET | /reports | 日报列表 |
| GET | /reports/{id} | 日报详情（选题+速览） |
| GET | /jobs/{id} | 任务状态查询 |

## 已知限制（后续阶段处理）

- **X（推特）数据暂缓**：15 个 X 账号为占位，采集返回空，商业上线前接入真实采集（见 `决策备忘.md`）。
- **被反爬拦截的源**：xAI Blog、Perplexity Blog 已停用（返回 403），需后续单独方案。
- **模型**：无 Key 时 mock 模式；真实日报质量需接入 DeepSeek Key 后验收。
- **排序公式未冻结**：临时公式（见 `docs/阶段2-技术开发文档.md`），阶段 6 真实数据演练时统一评测。
- 信息源写接口本阶段无登录鉴权（本地 MVP，后续阶段接入账号体系）。
