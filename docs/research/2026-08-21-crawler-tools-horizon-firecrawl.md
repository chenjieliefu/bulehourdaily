# 当前采集方式、Horizon 与 Firecrawl 评估

- 日期：2026-08-21
- 范围：只核查本项目代码、Thysrael/Horizon 官方仓库、Firecrawl 官方文档与官方仓库。
- 结论先行：**当前采集不是由 AI 完成的；AI 在采集完成后做事件归并、摘要和日报写作。现阶段不应把全部采集替换成 Firecrawl，也不需要先安装 Firecrawl MCP。** 保留 RSS / GitHub Release 的现有轻量采集，对少数没有 RSS、必须渲染 JavaScript 或普通 HTTP 长期失败的网页，再用 Firecrawl Cloud API 做小范围试点。

## 1. 本项目当前到底怎样采集

### 1.1 采集不是 AI，而是普通网络请求 + Feed 解析

当前 `backend/app/services/collectors.py` 的行为很简单：

1. 用 `httpx.get()` 请求信息源 URL；
2. 用 `feedparser` 解析 RSS / Atom；
3. 取标题、链接、摘要、作者和发布时间，转为统一结构；
4. `backend/app/services/collection.py` 对规范化 URL 做 SHA-256 去重并入库；
5. 单个来源失败只记录该来源失败，不阻断其他来源；
6. `backend/app/main.py` 每 45 分钟触发一次全量采集。

`rss` 和 `github_releases` 目前走的是同一条 HTTP + `feedparser` 路径；GitHub Release 来源实际使用 GitHub 提供的 Atom Feed，不是浏览器爬页面，也不是模型自己上网找内容。

种子配置目前共有 43 个来源：14 个 RSS、14 个 GitHub Release、15 个 X。41 个被标记为启用，但 15 个 X 来源在采集器中直接返回空列表，因此真正产生内容的仍是 12 个启用 RSS + 14 个 GitHub Release。xAI Blog 和 Perplexity Blog 因普通请求受阻被禁用。

当前采集层没有以下能力：JavaScript 页面渲染、登录态、代理轮换、浏览器动作、站点级递归爬取、全文正文抽取、针对 429/5xx 的退避重试。采集编排还是逐源串行执行。这些是后续按真实失败案例补强的地方，但不等于现在必须上一个重型爬虫平台。

### 1.2 AI 在采集之后才介入

`backend/app/services/event_extraction.py` 从数据库选择最近 48 小时的来源条目，再把标题和摘要交给模型归并成热点事件；`backend/app/services/report_generation.py` 再让模型负责日报文字。没有模型 Key 时会生成明确标注为“模拟”的内容。

因此当前链路是：

`HTTP / RSS / Atom 采集 → 确定性去重入库 → AI 归并热点 → AI 写日报`

准确地说，AI 是“编辑和分析员”，不是当前的“爬虫”。

## 2. Horizon 的采集架构是什么

Horizon 与本项目的基本思路相近，但来源适配器和后处理更完整。

### 2.1 获取层仍以确定性程序为主

Horizon 的所有 scraper 继承 `BaseScraper`，共享异步 HTTP 客户端，实现统一的 `fetch(since)`，多个来源通过 `asyncio.gather` 并发抓取。官方列出的实现包括：

- RSS / Atom：`feedparser`；可为指定 RSS 配置全文抽取器；
- GitHub：调用 GitHub REST API 获取用户事件或仓库 Release；
- Hacker News：调用 Firebase HN API，并抓取高分评论；
- Reddit：优先解析 `old.reddit.com` HTML，并以 JSON、RSS 为回退；遇到 429 会读取 `Retry-After`，等待后重试一次；
- Telegram：读取公开频道的 `t.me/s/<channel>` Web 预览；
- X / Twitter：不是让大模型直接浏览，而是调用 Apify 的 `altimis~scweet` Actor，轮询任务后读取结果；
- OpenBB：通过 OpenBB SDK 获取金融新闻；
- OSS Insight：调用公共 API 获取近期涨星仓库。

依据：[Horizon Scrapers 官方说明](https://github.com/Thysrael/Horizon/blob/main/docs/scrapers.md)、[Horizon Configuration 官方说明](https://github.com/Thysrael/Horizon/blob/main/docs/configuration.md)。

Horizon 的 RSS 全文抽取是可选的：Feed 先照常解析，再对指定条目的文章 URL 使用 Trafilatura 提取正文；如果抽取失败，回退到 Feed 自带摘要，不让全文提取失败毁掉整条数据。[Horizon Extractors 官方说明](https://github.com/Thysrael/Horizon/blob/main/docs/extractors.md)

### 2.2 AI 与采集层是分开的

Horizon 的官方流程明确为：配置来源 → Fetch → 去重 → AI 评分与过滤 → Enrich → Summarize → 发布。也就是说，主采集仍由 scraper / API / HTTP 完成，AI 用于降噪、评分、补充背景和生成摘要。[Horizon README 的 How It Works](https://github.com/Thysrael/Horizon#how-it-works)

这说明本项目“先确定性采集，再让 AI 编辑”的方向是合理的；值得借鉴的是 Horizon 的来源适配器、并发、回退和全文抽取，而不是把 Horizon 当成一个“让 AI 自己爬全网”的黑盒。

### 2.3 Horizon MCP 不是另一种爬虫引擎

Horizon 内置 MCP 把原有管线暴露为 `hz_fetch_items`、`hz_score_items`、`hz_filter_items`、`hz_enrich_items`、`hz_generate_summary`、`hz_run_pipeline` 等工具；官方明确写着 MCP 层不会重写业务逻辑，而是复用主代码库已有模块。[Horizon MCP 官方说明](https://github.com/Thysrael/Horizon/blob/main/src/mcp/README.md)

所以 Horizon MCP 的价值是让 AI 客户端分阶段触发、检查和调试 Horizon，不是提高底层网页抓取成功率。本项目如果不直接采用 Horizon 的整套管线，就没有必要为了“爬得更好”而接它的 MCP。

## 3. Firecrawl 能提供什么

Firecrawl 更像“托管的网页获取与清洗基础设施”，不是新闻源选择器。

| 能力 | 生产用途 | 是否必然使用 AI |
|---|---|---|
| Scrape | 给一个已知 URL，返回 Markdown、HTML、链接、截图或 JSON；支持 JS 渲染、等待、标签过滤、PDF、位置和代理选项 | 普通 Markdown 抓取不要求由 AI 决策；JSON 结构化提取可使用 LLM |
| Batch Scrape | 并行抓多个已知 URL | 否，取决于输出格式 |
| Crawl | 从站点入口按 sitemap / 链接递归发现页面，并对每页执行 scrape；异步任务，可限制路径、深度、页数和并发 | 否；可用自然语言生成 crawl 参数，但执行仍是爬取任务 |
| Map | 快速列出站点 URL，可结合 sitemap、子域、搜索词和上限 | 否 |
| Search | 搜索 Web，并可同时抓取结果页正文 | 搜索本身不是本项目固定源采集的必需项 |
| Extract | 对已知 URL / 域做 LLM 结构化抽取；官方目前建议新项目优先考虑 `/agent` 或单页 `/scrape` JSON 模式 | 是，属于 LLM 驱动结构化提取 |
| Browser / Interact | 页面必须点击、滚动、填写表单或保持会话时控制浏览器 | 可用代码或自然语言代理；Cloud 能力 |

依据：[Firecrawl API 总览](https://docs.firecrawl.dev/api-reference/v2-introduction)、[Scrape API](https://docs.firecrawl.dev/api-reference/endpoint/scrape)、[Crawl API](https://docs.firecrawl.dev/api-reference/endpoint/crawl-post)、[Map API](https://docs.firecrawl.dev/api-reference/endpoint/map)、[结构化提取选择指南](https://docs.firecrawl.dev/developer-guides/usage-guides/choosing-the-data-extractor)。

### 3.1 部署与限制

Firecrawl 有 Cloud 与自托管两种路线。官方说明：自托管包含核心 scrape / crawl / map / search 以及 Fetch / Playwright 处理，但身份验证、TLS、持久化、监控、容量、升级和恢复都要自己维护；基于 LLM 的格式、高级抓取服务也需要额外配置。Cloud 由 Firecrawl 运维，并提供托管 Dashboard、增强代理路径以及部分 Agent / Browser / 企业能力。[Firecrawl 开源版与 Cloud 对比](https://docs.firecrawl.dev/zh/contributing/open-source-or-cloud)

对目前只有一个人的项目，自托管 Firecrawl 会新增一整套 Redis、队列、浏览器和监控运维面，收益尚未被真实失败样本证明，因此不建议现在自托管。

Cloud 的价格和额度会变化，以下仅是 2026-08-21 查到的官方页面状态：免费方案每月 1,000 credits、2 并发；Hobby 为 5,000 credits、年付折合 16 美元/月；Standard 为 100,000 credits、年付折合 83 美元/月。Scrape、Crawl 通常按成功抓取页计费；高级 JSON / Enhanced 等能力可能另计；自助套餐不是纯按量付费，额度通常不结转。需要特别注意：官方价格页把 Map 写成 `1 credit / page`，但 Map 功能文档写成 `1 credit / call`，存在官方口径冲突，正式接入前应以控制台实际账单或 Firecrawl 书面确认为准。[Firecrawl 官方定价](https://www.firecrawl.dev/pricing)、[Map 官方说明](https://docs.firecrawl.dev/features/map)、[官方速率限制](https://docs.firecrawl.dev/zh/rate-limits)

一个直观的成本提醒：如果把当前 26 个有效 RSS / GitHub Feed 都机械替换成 Firecrawl，并继续每 45 分钟请求一次，按一页一次粗算约为 `26 × 32 × 30 = 24,960` 页/月，还没有计算站内 crawl 和高级格式。因此 Firecrawl 应该只处理“普通采集解决不了的页面”，不应替换免费、稳定的 Feed。

此外，Firecrawl 官方 Crawl 默认遵守 robots.txt；忽略 robots.txt 与自定义 robots User-Agent 属于 Enterprise 能力。零数据保留也需要联系官方开启。生产接入仍需逐站核查服务条款、robots 和内容使用边界。[Firecrawl Crawl API](https://docs.firecrawl.dev/api-reference/endpoint/crawl-post)

## 4. Firecrawl MCP 与生产 API 的区别

两者访问的是同一类 Firecrawl 能力，差别在“谁来调度”。

- **MCP**：把 Scrape、Map、Crawl、Search 等包装成 AI 客户端可选择的工具，适合在 Codex / Claude / Cursor 中临时调查来源、读取网页、调试失败页面。官方说明 MCP 请求仍使用标准 Firecrawl API 限额。[Firecrawl Developers & MCP](https://docs.firecrawl.dev/use-cases/developers-mcp)
- **API / SDK**：由本项目后端按明确代码路径调用，参数、预算、超时、重试、数据结构和错误处理都能固定下来，更适合每天自动运行的生产采集任务。[Firecrawl API v2](https://docs.firecrawl.dev/api-reference/v2-introduction)

官方 MCP 支持托管服务，也可本地运行；API Key 应放在 Authorization header 或客户端密钥存储中，不能放进 URL。[Firecrawl MCP 官方配置](https://github.com/firecrawl/firecrawl-docs/blob/main/mcp-server.mdx)

**本项目建议：现在不要把 MCP 装进线上。** 如果后面做来源调研，MCP 可以作为开发阶段的人工助手；一旦某类网页被确认要进入定时生产链路，应由后端直接调用 Firecrawl API，并继续落到现有 `SourceItem`、去重和运行记录体系。MCP 不是生产可靠性的替代品。

## 5. 分阶段建议

### 现在：不增加 Firecrawl，不改主链路

1. 保留 RSS / GitHub Release 的 `httpx + feedparser`；它们稳定、便宜、结构明确，也无需 AI。
2. 先完成信息源重选：当前真正的问题是来源有些太宽泛，以及 15 个启用 X 源实际永远返回 0 条，不是缺一个通用爬虫。
3. 给现有采集补最低限度的超时分类、有限重试、退避、并发上限和来源健康指标。

### 下一步：先借鉴 Horizon 的轻量能力

1. 对 RSS 摘要太短、但文章 HTML 可直接访问的来源，先试 Trafilatura 全文抽取，并保留“失败回退 Feed 摘要”。
2. 对 Hacker News、GitHub 等有官方 / 公共 API 的平台，优先写专用适配器，避免爬 HTML。
3. X 不建议以 Firecrawl 作为首选。Horizon 当前也使用专门的 Apify Actor；本项目应在官方 X API、合规第三方数据服务和 Apify 之间单独评估成本与合规，不能认为装了 Firecrawl 就解决社交平台反爬。

### 只有出现下列情况时，才试 Firecrawl Cloud API

- 来源没有 RSS / API，正文必须 JavaScript 渲染；
- 普通 HTTP + Trafilatura 在同一目标上持续失败；
- 必须发现一个站点栏目下的新页面，适合 Map / Crawl；
- 必须点击、滚动或处理分页才能看到内容；
- PDF / Word / 表格等文档解析成为稳定需求。

建议只选 2–5 个明确失败的来源做两周试点，记录成功率、每条内容 credits、延迟、正文完整性、重复率和站点合规情况。试点通过后再把 Firecrawl Cloud API 封装成一个新的来源适配器；不要一开始自托管，也不要让 AI 自由 crawl 任意域名。

## 6. 最终决策

- **目前爬取是否通过 AI？** 否。当前是普通 HTTP + RSS / Atom 解析；AI 在入库以后做归并与写作。
- **是否需要 Firecrawl？** 现在不需要全量接入；未来可能只需要它解决少数动态页面、全文抽取失败页面或站点发现任务。
- **是否需要 Firecrawl MCP？** 现在不需要。它适合开发调研和人工排障，不应作为线上定时采集的首要集成方式。
- **最值得马上借鉴 Horizon 的是什么？** 并发抓取、专用来源适配器、有限重试、全文抽取失败回退、按来源质量筛选；不是直接复制整套项目，也不是让 AI 接管抓取。
