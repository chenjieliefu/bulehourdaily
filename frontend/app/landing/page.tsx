import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-obsidian">
      {/* 顶栏 */}
      <header className="glass sticky top-0 z-50">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-3">
            <span className="font-serif text-xl text-cloud">微蓝日报</span>
            <span className="font-mono text-xs uppercase tracking-widest text-cyan">Blue Hour Daily</span>
          </div>
          <Link
            href="/"
            className="rounded-full border border-cyan/40 px-4 py-1.5 font-mono text-xs uppercase tracking-widest text-cyan transition-colors hover:bg-cyan/10"
          >
            看今日日报 →
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="sky-gradient relative overflow-hidden px-6 pb-32 pt-24 text-center">
        <div className="grid-lines pointer-events-none absolute inset-0" />
        <div className="horizon-glow pointer-events-none absolute inset-x-0 bottom-0 h-64" />

        <div className="relative">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-cyan">
            Blue Hour Daily · 08:00
          </p>
          <h1 className="mx-auto mt-8 max-w-3xl font-serif text-6xl leading-tight text-cloud md:text-7xl">
            在世界醒来之前，<br className="hidden md:block" />看见下一刻。
          </h1>
          <p className="mx-auto mt-8 max-w-xl text-lg leading-relaxed text-silver">
            每天 08:00，把海外最新 AI 动态，变成三个值得拍的抖音选题。
          </p>
          <p className="mt-5 font-mono text-xs uppercase tracking-widest text-silver/50">
            See what&apos;s next before the world wakes.
          </p>

          <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/"
              className="rounded-full bg-cyan px-8 py-3 text-sm font-medium text-obsidian transition-opacity hover:opacity-90"
            >
              看今日日报
            </Link>
            <Link
              href="/#subscribe"
              className="glass rounded-full px-8 py-3 text-sm text-cloud transition-colors hover:text-cyan"
            >
              了解订阅
            </Link>
          </div>
        </div>
      </section>

      {/* 产品说明 */}
      <section className="mx-auto max-w-[1200px] px-6 py-24">
        <p className="font-mono text-xs uppercase tracking-widest text-cyan">产品是什么</p>
        <h2 className="mt-4 max-w-2xl font-serif text-3xl leading-snug text-cloud">
          每天一份日报，把「看信息」变成「拍什么」。
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {[
            { n: "01", t: "不漏掉", d: "盯着 40+ 海外 AI 信息源，每天 08:00 汇总最新动态。" },
            { n: "02", t: "会判断", d: "聚成热点事件，标注可信度，告诉你哪个值得跟进。" },
            { n: "03", t: "能行动", d: "每个选题给出钩子、结构、画面建议，直接开拍。" },
          ].map((item) => (
            <div key={item.n} className="rounded-feature border border-steel bg-graphite p-8">
              <p className="font-serif text-3xl text-deep-iris">{item.n}</p>
              <h3 className="mt-4 font-serif text-xl text-cloud">{item.t}</h3>
              <p className="mt-3 text-sm leading-relaxed text-ash">{item.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 页脚 */}
      <footer className="border-t border-steel px-6 py-12 text-center">
        <p className="font-serif text-lg text-cloud">微蓝日报 · Blue Hour Daily</p>
        <p className="mt-3 font-mono text-xs uppercase tracking-widest text-fog">
          在世界醒来之前，看见下一刻。
        </p>
      </footer>
    </div>
  );
}
