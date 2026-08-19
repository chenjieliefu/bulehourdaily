"use client";

import { useEffect, useState } from "react";
import { getReport, listReports, type Report } from "@/lib/api";

const LABEL: Record<string, { text: string; cls: string }> = {
  official: { text: "官方确认", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
  multi_source: { text: "多方报道", cls: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30" },
  early_signal: { text: "早期信号", cls: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
};

function fmtTime(t: string | null) {
  if (!t) return "—";
  const s = String(t);
  const d = new Date(/[zZ]|[+-]\d{2}:\d{2}$/.test(s) ? s : s + "Z");
  return d.toLocaleString("zh-CN", { hour12: false });
}

export default function Home() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const reports = await listReports();
        if (reports.length > 0) {
          setReport(await getReport(reports[0].id));
        } else {
          setReport(null);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-obsidian">
      {/* 顶栏 */}
      <header className="sticky top-0 z-50 glass">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-3">
            <span className="font-serif text-xl text-cloud">微蓝日报</span>
            <span className="font-mono text-xs uppercase tracking-widest text-cyan">Blue Hour Daily</span>
          </div>
          <nav className="font-mono text-xs uppercase tracking-widest text-fog">
            <span className="cursor-not-allowed opacity-60">最近 7 天</span>
          </nav>
        </div>
      </header>

      {/* Hero：蓝色天空渐变 */}
      <section className="sky-gradient px-6 pb-24 pt-20 text-center">
        <p className="font-mono text-xs uppercase tracking-[0.25em] text-cyan">
          Blue Hour Daily
        </p>
        <h1 className="mx-auto mt-6 max-w-3xl font-serif text-5xl leading-tight text-cloud md:text-6xl">
          在世界醒来之前，看见下一刻。
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-base text-silver">
          每天 08:00，把海外最新 AI 动态，变成三个值得拍的抖音选题。
        </p>
        <p className="mt-4 font-mono text-xs uppercase tracking-widest text-silver/60">
          See what&apos;s next before the world wakes.
        </p>
      </section>

      {/* 日报正文 */}
      <main className="mx-auto max-w-[1200px] px-6 pb-24">
        {loading && (
          <p className="mt-16 text-center text-fog">正在加载今日日报…</p>
        )}

        {!loading && error && (
          <div className="mt-16 rounded-card border border-red-500/30 bg-red-500/10 p-6 text-center">
            <p className="text-red-400">加载失败：{error}</p>
            <p className="mt-2 text-sm text-fog">请确认后端服务已启动。</p>
          </div>
        )}

        {!loading && !error && !report && (
          <div className="mt-16 rounded-card border border-steel bg-graphite p-10 text-center">
            <p className="text-silver">今日日报尚未生成。</p>
            <p className="mt-2 text-sm text-fog">每天北京时间 08:00 自动生成。</p>
          </div>
        )}

        {!loading && !error && report && (
          <>
            {/* 日报头 */}
            <div className="mt-16 border-b border-steel pb-8">
              <p className="font-mono text-xs uppercase tracking-widest text-fog">
                {report.report_date} · 通用日报
              </p>
              <h2 className="mt-4 font-serif text-2xl leading-snug text-cloud">
                {report.summary || "今日摘要"}
              </h2>
              <p className="mt-3 font-mono text-xs text-fog">
                生成时间 {fmtTime(report.updated_at)} · 最近采集 {fmtTime(report.last_collect_at)}
              </p>
            </div>

            {/* 三个选题 */}
            <section className="mt-10">
              <h3 className="font-mono text-xs uppercase tracking-widest text-cyan">
                今日选题 · 3
              </h3>
              <div className="mt-6 grid gap-6">
                {report.topics.map((t) => {
                  const label = t.credibility_label ? LABEL[t.credibility_label] : null;
                  return (
                    <article key={t.id} className="rounded-feature border border-steel bg-graphite p-8">
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="font-serif text-3xl text-deep-iris">0{t.order_index}</span>
                        {label && (
                          <span className={`rounded-full border px-3 py-1 text-xs ${label.cls}`}>
                            {label.text}
                          </span>
                        )}
                      </div>
                      <h4 className="mt-4 font-serif text-2xl leading-snug text-cloud">{t.title}</h4>
                      <p className="mt-2 font-mono text-xs text-fog">事件时间 {fmtTime(t.event_published_at)}</p>

                      <div className="mt-6 grid gap-4 text-sm md:grid-cols-2">
                        <Field label="发生了什么">{t.what_happened}</Field>
                        <Field label="为什么现在值得关注">{t.why_now}</Field>
                        <Field label="切入角度">{t.angle}</Field>
                        <Field label="前三秒钩子" accent>{t.hook}</Field>
                        <Field label="结构建议">{t.structure}</Field>
                        <Field label="画面建议">{t.visual}</Field>
                      </div>

                      <div className="mt-6 rounded-card border border-cyan/30 bg-cyan/10 p-4">
                        <span className="font-mono text-xs uppercase tracking-widest text-cyan">建议发布时机</span>
                        <p className="mt-1 text-sm text-silver">{t.time_window}</p>
                      </div>

                      <div className="mt-4 text-sm text-fog">
                        <span className="font-mono text-xs uppercase tracking-widest">证据</span>
                        <div className="mt-2 flex flex-wrap gap-3">
                          {t.evidence.length === 0 && <span>—</span>}
                          {t.evidence.map((ev) => (
                            <a
                              key={ev.source_item_id}
                              href={ev.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="rounded-full border border-steel px-3 py-1 text-xs text-silver transition-colors hover:border-cyan hover:text-cyan"
                            >
                              {ev.source_name} · {fmtTime(ev.published_at)}
                            </a>
                          ))}
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>

            {/* 热点速览 */}
            {report.briefs.length > 0 && (
              <section className="mt-14">
                <h3 className="font-mono text-xs uppercase tracking-widest text-cyan">
                  热点速览 · {report.briefs.length}
                </h3>
                <ul className="mt-6 divide-y divide-steel rounded-card border border-steel bg-graphite px-8">
                  {report.briefs.map((b) => (
                    <li key={b.id} className="flex items-baseline gap-4 py-4">
                      <span className="font-mono text-xs text-deep-iris">{String(b.order_index).padStart(2, "0")}</span>
                      <span className="flex-1 text-sm text-ash">{b.summary}</span>
                      <span className="shrink-0 font-mono text-xs text-fog">{fmtTime(b.event_published_at)}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </main>

      {/* 页脚 */}
      <footer className="border-t border-steel px-6 py-10 text-center">
        <p className="font-serif text-lg text-cloud">微蓝日报 · Blue Hour Daily</p>
        <p className="mt-2 font-mono text-xs uppercase tracking-widest text-fog">
          在世界醒来之前，看见下一刻。
        </p>
      </footer>
    </div>
  );
}

function Field({ label, children, accent = false }: { label: string; children: string; accent?: boolean }) {
  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-widest text-fog">{label}</p>
      <p className={`mt-1 ${accent ? "text-cyan" : "text-silver"}`}>{children}</p>
    </div>
  );
}
