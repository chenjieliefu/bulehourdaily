"use client";

import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import styles from "./LandingPrototype.module.css";

// PROTOTYPE — three full-page directions for the product introduction, switchable via ?variant=.
type ProductIntroContent = {
  eyebrow: string;
  title: string;
  subtitle: string;
  section_title: string;
  features: { title: string; detail: string }[];
};

const VARIANTS = [
  { key: "A", label: "黎明信号场" },
  { key: "B", label: "编辑部晨报" },
  { key: "C", label: "创作者雷达" },
];

const WORKFLOW = [
  ["01", "捕捉", "监测海外 AI 信号。"],
  ["02", "判断", "聚合事件，核验来源。"],
  ["03", "转译", "提炼选题与表达角度。"],
  ["04", "行动", "生成个性化创作方案。"],
];

const SAMPLE_TOPICS = [
  "一项模型更新，真正值得创作者讲的是什么？",
  "AI 产品突然爆红：数据背后有哪些可拍角度？",
  "从官方发布到短视频，如何避免把个案写成趋势？",
];

const EDITORIAL_WORKFLOW = [
  { number: "01", title: "捕捉", detail: "追踪官方发布、技术社区和产品动态", output: "原始信号" },
  { number: "02", title: "判断", detail: "聚合去重，核验事实与影响范围", output: "可信事件" },
  { number: "03", title: "转译", detail: "提炼事件价值与内容切入角度", output: "三个选题" },
  { number: "04", title: "行动", detail: "结合账号定位，补齐表达建议和风险提示", output: "创作方案" },
];

const EDITORIAL_STANDARDS = [
  ["来源可追溯", "保留原始链接、发布时间与关键证据"],
  ["事实有边界", "区分官方确认、早期信号与观点推测"],
  ["发布前复核", "重要事实经人工检查后进入公开日报"],
  ["内容可纠正", "支持下架、修订、复核与重新上架"],
];

const AUDIENCES = [
  ["01", "AI 内容创作者", "每天需要稳定选题，不想把时间耗在筛选信息上", "选题 · 角度 · 风险提示"],
  ["02", "行业从业者", "希望快速看懂 AI 行业变化，以及它为什么值得关注", "事件 · 影响 · 原始来源"],
  ["03", "小型内容团队", "需要统一判断依据，让选题讨论更快进入创作阶段", "共识 · 证据 · 行动方案"],
];

export default function LandingPrototype({ content }: { content: ProductIntroContent }) {
  const searchParams = useSearchParams();
  const requested = (searchParams.get("variant") || "B").toUpperCase();
  const variant = process.env.NODE_ENV === "production"
    ? "B"
    : VARIANTS.some((item) => item.key === requested) ? requested : "B";

  return (
    <>
      {variant === "A" && <SignalFieldVariant content={content} />}
      {variant === "B" && <EditorialVariant />}
      {variant === "C" && <RadarVariant content={content} />}
    </>
  );
}

function PrototypeLogo({ light = false }: { light?: boolean }) {
  return (
    <Link href="/landing" className={`${styles.logo} ${light ? styles.logoLight : ""}`}>
      <Image src="/icon.svg" alt="" width={42} height={42} priority aria-hidden="true" />
      <span>
        <strong>微蓝日报</strong>
        <small>BLUE HOUR DAILY</small>
      </span>
    </Link>
  );
}

function SignalFieldVariant({ content }: { content: ProductIntroContent }) {
  return (
    <main className={styles.signalPage}>
      <header className={styles.signalNav}>
        <PrototypeLogo light />
        <nav>
          <a href="#signal-workflow">如何工作</a>
          <a href="#signal-personal">个性化</a>
          <Link href="/">看今日日报</Link>
        </nav>
      </header>

      <section className={styles.signalHero}>
        <div className={styles.signalGrid} />
        <div className={styles.dawnGlow} />
        <SignalParticles />
        <div className={styles.signalCopy}>
          <p>{content.eyebrow}</p>
          <h1>把全球 AI 动态，<br />变成今天能拍的三个选题。</h1>
          <span>在世界醒来之前，看见下一刻。</span>
          <div className={styles.heroActions}>
            <Link href="/">看今日日报</Link>
            <Link href="/mine">体验个性化日报</Link>
          </div>
        </div>

        <div className={styles.signalStage} aria-label="从信息源到三个选题的动态演示">
          <div className={styles.sourceColumn}>
            {["OpenAI", "DeepMind", "Anthropic", "GitHub", "Hacker News"].map((source, index) => (
              <span key={source} style={{ "--delay": `${index * 0.8}s` } as React.CSSProperties}>{source}</span>
            ))}
          </div>
          <div className={styles.eventCluster}>
            <span className={styles.eventCore}>可信事件</span>
            <i className={styles.eventRingOne} />
            <i className={styles.eventRingTwo} />
            <small>聚合 · 去重 · 证据</small>
          </div>
          <div className={styles.topicColumn}>
            {SAMPLE_TOPICS.map((title, index) => (
              <article key={title} style={{ "--delay": `${index * 1.1 + 1.2}s` } as React.CSSProperties}>
                <span>0{index + 1}</span>
                <p>{title}</p>
              </article>
            ))}
          </div>
          <div className={styles.flowBeam} />
        </div>

        <div className={styles.signalStats}>
          <span><strong>持续</strong>海外信号监测</span>
          <span><strong>3 层</strong>事实与可信度判断</span>
          <span><strong>3 个</strong>每日可拍选题</span>
        </div>
      </section>

      <section className={styles.signalWorkflow} id="signal-workflow">
        <div className={styles.sectionIntro}>
          <p>THE DAILY PIPELINE</p>
          <h2>不是给你更多信息，<br />而是替你完成第一轮判断。</h2>
          <span>从来源、事实到行动建议，每一步都能回到原始证据。</span>
        </div>
        <div className={styles.workflowRail}>
          {WORKFLOW.map(([number, title, detail]) => (
            <article key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.liveExample}>
        <div>
          <p className={styles.monoLabel}>REAL OUTPUT · 08:00</p>
          <h2>先看结论，<br />需要时再展开证据与创作方案。</h2>
          <p>最新公开日报人人可看。每个选题保留来源、可信度、为什么值得关注，以及可以直接执行的表达方案。</p>
          <Link href="/">查看真实公开日报 →</Link>
        </div>
        <article className={styles.sampleReport}>
          <header><span>BLUE HOUR · DAILY BRIEF</span><b>第 024 期</b></header>
          <h3>今天，先看这 <em>3</em> 件事</h3>
          <div className={styles.sampleTopic}>
            <span>01</span>
            <div><small>官方确认</small><strong>模型能力更新之后，创作者真正应该解释什么？</strong><p>先交代发生了什么，再给出值得拍的角度与风险边界。</p></div>
          </div>
          <footer><span>原始来源 2</span><span>建议今日发布</span></footer>
        </article>
      </section>

      <section className={styles.personalSection} id="signal-personal">
        <div className={styles.profileCard}>
          <span>你的创作者画像</span>
          <strong>AI 工具测评 · 职场人群 · 理性拆解</strong>
          <div><i>账号定位</i><i>目标观众</i><i>表达风格</i><i>内容禁区</i></div>
        </div>
        <div className={styles.personalArrow}>→</div>
        <div className={styles.personalResult}>
          <span>个性化日报</span>
          <h2>同一批热点，<br />只留下适合你账号的三个。</h2>
          <ul><li>为什么推荐给你</li><li>一键展开创作方案</li><li>想做 / 不感兴趣 / 已发布</li></ul>
        </div>
      </section>

      <AccessAndFooter theme="signal" />
    </main>
  );
}

function SignalParticles() {
  return (
    <div className={styles.particles} aria-hidden="true">
      {Array.from({ length: 18 }, (_, index) => (
        <i
          key={index}
          style={{
            "--x": `${6 + ((index * 17) % 88)}%`,
            "--y": `${10 + ((index * 29) % 76)}%`,
            "--delay": `${(index % 7) * -1.15}s`,
            "--size": `${3 + (index % 3) * 2}px`,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

function EditorialVariant() {
  const [navCompact, setNavCompact] = useState(false);

  const scrollToSection = (event: React.MouseEvent<HTMLAnchorElement>, selector: string) => {
    event.preventDefault();
    document.querySelector(selector)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  useEffect(() => {
    const updateNavigation = () => setNavCompact(window.scrollY > 56);
    updateNavigation();
    window.addEventListener("scroll", updateNavigation, { passive: true });
    return () => window.removeEventListener("scroll", updateNavigation);
  }, []);

  return (
    <main className={styles.editorialPage}>
      <header className={styles.editorialNav}>
        <div className={`${styles.editorialNavShell} ${navCompact ? styles.editorialNavCompact : ""}`}>
          <PrototypeLogo />
          <div className={styles.editorialNavActions}>
            <nav>
              <a href="#editorial-workflow" onClick={(event) => scrollToSection(event, "#editorial-workflow")}>工作流</a>
              <a href="#editorial-audience" onClick={(event) => scrollToSection(event, "#editorial-audience")}>适合谁</a>
            </nav>
            <Link href="/">打开今日日报 <span>↗</span></Link>
          </div>
        </div>
      </header>

      <section className={styles.dawnHero}>
        <Image
          src="/landing/blue-hour-sunrise-v1.png"
          alt="蓝调时刻，远山与湖面之间的太阳正在升起"
          fill
          priority
          sizes="100vw"
          className={styles.dawnPhoto}
        />
        <div className={styles.dawnPhotoOverlay} aria-hidden="true" />
        <div className={styles.dawnAtmosphere} aria-hidden="true" />
        <div className={styles.dawnCopy}>
          <p>BLUE HOUR DAILY · MORNING BRIEF · 08:00</p>
          <h1><span>在世界醒来之前</span><span>先看见下一刻</span></h1>
          <span>每天 08:00，三个值得关注的 AI 选题</span>
          <div>
            <Link href="/">看今日日报 <b>→</b></Link>
          </div>
        </div>
        <a className={styles.dawnScrollHint} href="#editorial-workflow" onClick={(event) => scrollToSection(event, "#editorial-workflow")}><i />向下了解</a>
      </section>

      <div className={styles.editorialBody}>
        <section className={styles.editorialWorkflow} id="editorial-workflow">
          <header className={styles.workflowIntro}>
            <span>WORKFLOW · 04 STEPS</span>
            <h2>从全球信号<br />到今天能讲的<span className={styles.mobileOnlyBreak}><br /></span>三个选题</h2>
            <p>系统先完成信息处理，编辑再复核关键判断<br />最后交付可追溯、可执行的内容方向</p>
          </header>

          <div className={styles.workflowSteps}>
            {EDITORIAL_WORKFLOW.map((item) => (
              <article key={item.number}>
                <span>{item.number}</span>
                <h3>{item.title}</h3>
                <p>{item.detail}</p>
                <small>输出 · {item.output}</small>
              </article>
            ))}
          </div>

          <div className={styles.workflowStandard}>
            <div className={styles.standardStatement}>
              <span>EDITORIAL STANDARD</span>
              <h3>每个判断<br />都能回到出处</h3>
              <blockquote>“可以晚一点，不能把一个人的选择写成整个行业的趋势”</blockquote>
            </div>
            <div className={styles.standardGrid}>
              {EDITORIAL_STANDARDS.map(([title, detail]) => (
                <article key={title}><i>✓</i><div><h4>{title}</h4><p>{detail}</p></div></article>
              ))}
            </div>
          </div>
        </section>

        <div className={styles.editorialSectionIntro}>
          <span>PUBLIC &amp; PERSONAL</span>
          <h2>同一天<br />两种日报</h2>
          <p>公开日报看全局<br />个性化日报只选适合你的</p>
        </div>
        <section className={styles.editorialPersonal} id="editorial-personal">
          <div><p>PUBLIC DAILY</p><h2>看清今天<br />发生了什么</h2><span>最新一期公开，归档登录后查看</span></div>
          <div className={styles.editorialPlus}>＋</div>
          <div><p>MY DAILY</p><h2>只看适合你的<br />三个选题</h2><span>匹配账号定位，并生成创作方案</span></div>
        </section>

        <section className={styles.editorialAudience} id="editorial-audience">
          <header>
            <span>FOR WHOM</span>
            <h2>适合需要稳定判断<br />不想追着信息流<span className={styles.mobileOnlyBreak}><br /></span>跑的人</h2>
            <p>不论一个人创作还是小团队协作<br />都从同一份可信事实开始</p>
          </header>
          <div>
            {AUDIENCES.map(([number, title, detail, tags]) => (
              <article key={number}><span>{number}</span><h3>{title}</h3><p>{detail}</p><small>{tags}</small></article>
            ))}
          </div>
        </section>

        <EditorialFooter />
      </div>
    </main>
  );
}

function EditorialFooter() {
  return (
    <>
      <section className={styles.finalCta}>
        <p>BLUE HOUR DAILY</p>
        <h2>把第一小时留给创作<br />不留给原始信息流</h2>
        <div><Link href="/">看今日日报</Link></div>
      </section>
      <footer className={styles.prototypeFooter}><PrototypeLogo /><span>在世界醒来之前，看见下一刻</span></footer>
    </>
  );
}

function RadarVariant({ content }: { content: ProductIntroContent }) {
  return (
    <main className={styles.radarPage}>
      <header className={styles.radarNav}>
        <PrototypeLogo light />
        <div><span className={styles.onlineDot} />SYSTEM ONLINE · NEXT REPORT 08:00</div>
        <Link href="/">OPEN DAILY ↗</Link>
      </header>

      <section className={styles.radarHero}>
        <div className={styles.radarCopy}>
          <p>CREATOR INTELLIGENCE SYSTEM</p>
          <h1>先发现信号，<br />再决定今天拍什么。</h1>
          <span>{content.subtitle}</span>
          <div className={styles.radarActions}><Link href="/">查看今日信号</Link><Link href="/mine">建立我的雷达</Link></div>
        </div>
        <div className={styles.radarVisual} aria-label="正在扫描海外 AI 信号">
          <div className={styles.radarSweep} />
          <div className={styles.radarRingOne} />
          <div className={styles.radarRingTwo} />
          <div className={styles.radarCrossX} />
          <div className={styles.radarCrossY} />
          {[[30, 27], [67, 38], [56, 68], [78, 73], [38, 58]].map(([x, y], index) => (
            <span key={`${x}-${y}`} style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${index * -0.55}s` }}><i />{index < 3 ? `SIGNAL 0${index + 1}` : ""}</span>
          ))}
          <strong>08:00</strong><small>SCAN · CLUSTER · VERIFY</small>
        </div>
      </section>

      <section className={styles.systemBoard}>
        <header><span>DAILY PROCESS</span><b>04 MODULES ACTIVE</b></header>
        <div>
          {WORKFLOW.map(([number, title, detail], index) => (
            <article key={number}><span>MODULE {number}</span><i style={{ width: `${78 - index * 8}%` }} /><h2>{title}</h2><p>{detail}</p></article>
          ))}
        </div>
      </section>

      <section className={styles.radarOutput}>
        <div className={styles.outputList}>
          <header><span>TODAY&apos;S OUTPUT</span><b>03</b></header>
          {SAMPLE_TOPICS.map((topic, index) => (
            <article key={topic}><span>0{index + 1}</span><div><small>{index === 0 ? "官方确认" : "早期信号"}</small><h3>{topic}</h3><p>原始来源 · 切入角度 · 创作方案 · 风险提示</p></div></article>
          ))}
        </div>
        <div className={styles.creatorLoop}>
          <p>PERSONALIZATION LOOP</p>
          <h2>不是更多热点，<br />是更适合你的热点。</h2>
          <ol><li><span>01</span>填写创作者画像</li><li><span>02</span>AI 重选当天信号</li><li><span>03</span>展开创作方案</li><li><span>04</span>反馈并持续优化</li></ol>
          <Link href="/mine">体验 3 份个性化日报 →</Link>
        </div>
      </section>

      <AccessAndFooter theme="radar" />
    </main>
  );
}

function AccessAndFooter({ theme }: { theme: "signal" | "editorial" | "radar" }) {
  return (
    <>
      <section className={`${styles.accessSection} ${styles[`access${theme[0].toUpperCase()}${theme.slice(1)}`]}`}>
        <div><span>01</span><p>无需登录</p><h2>看最新公开日报</h2><small>直接查看今天的内容。</small></div>
        <div><span>02</span><p>登录后</p><h2>回看往期归档</h2><small>查看历史日报与选题。</small></div>
        <div><span>03</span><p>邀请注册后</p><h2>体验个性化日报</h2><small>免费生成 3 份。</small></div>
      </section>
      <section className={styles.finalCta}>
        <p>BLUE HOUR DAILY</p>
        <h2>把第一小时留给创作，<br />不留给原始信息流。</h2>
        <div><Link href="/">看今日日报</Link><Link href="/register">创建微蓝账号</Link></div>
      </section>
      <footer className={styles.prototypeFooter}><PrototypeLogo light={theme !== "editorial"} /><span>在世界醒来之前，看见下一刻。</span></footer>
    </>
  );
}
