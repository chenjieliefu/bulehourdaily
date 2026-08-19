"use client";

import { useState } from "react";
import { fmtDate, fmtTime } from "@/lib/format";
import type { Report, Topic } from "@/lib/api";

const LABEL: Record<string, { text: string; cls: string }> = {
  official: { text: "官方确认", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
  multi_source: { text: "多方报道", cls: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30" },
  early_signal: { text: "早期信号", cls: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
};

const ACCENTS = [
  { num: "text-iris", ring: "border-iris/25", wash: "bg-iris/[0.06]", chip: "border-iris/30 text-iris", box: "border-iris/30 bg-iris/10", boxText: "text-pale-iris", bar: "bg-iris" },
  { num: "text-cyan", ring: "border-cyan/25", wash: "bg-cyan/[0.06]", chip: "border-cyan/30 text-cyan", box: "border-cyan/30 bg-cyan/10", boxText: "text-cyan", bar: "bg-cyan" },
  { num: "text-periwinkle", ring: "border-periwinkle/25", wash: "bg-periwinkle/[0.06]", chip: "border-periwinkle/30 text-periwinkle", box: "border-periwinkle/30 bg-periwinkle/10", boxText: "text-periwinkle", bar: "bg-periwinkle" },
];

export default function ReportView({ report }: { report: Report }) {
  const [expandedId, setExpandedId] = useState<number | null>(report.topics[0]?.id ?? null);

  return (
    <div className="mx-auto max-w-[880px]">
      {/* 日报头 */}
      <div className="border-b border-steel pb-8 pt-10">
        <p className="font-mono text-xs uppercase tracking-widest text-fog">
          {fmtDate(report.report_date)} · 通用日报
        </p>
        <h1 className="mt-4 font-serif text-2xl leading-snug text-cloud md:text-3xl">
          {report.summary || "今日摘要"}
        </h1>
        <p className="mt-3 font-mono text-xs text-fog">
          生成 {fmtTime(report.updated_at)} · 最近采集 {fmtTime(report.last_collect_at)}
        </p>
      </div>

      {/* 选题列表 */}
      <section className="mt-8">
        <div className="flex items-baseline justify-between">
          <h2 className="font-mono text-xs uppercase tracking-widest text-cyan">今日选题</h2>
          <span className="font-serif text-sm text-fog">{String(report.topics.length).padStart(2, "0")}</span>
        </div>
        <div className="mt-4 grid gap-4">
          {report.topics.map((t) => (
            <TopicCard
              key={t.id}
              topic={t}
              expanded={expandedId === t.id}
              onToggle={() => setExpandedId(expandedId === t.id ? null : t.id)}
            />
          ))}
        </div>
      </section>

      {/* 热点速览 */}
      {report.briefs.length > 0 && (
        <section className="mt-12">
          <div className="flex items-baseline justify-between">
            <h2 className="font-mono text-xs uppercase tracking-widest text-cyan">热点速览</h2>
            <span className="font-serif text-sm text-fog">{String(report.briefs.length).padStart(2, "0")}</span>
          </div>
          <ul className="mt-4 divide-y divide-steel rounded-card border border-steel bg-graphite px-6">
            {report.briefs.map((b) => (
              <li key={b.id} className="py-4">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono text-xs text-deep-iris">{String(b.order_index).padStart(2, "0")}</span>
                  <p className="flex-1 text-sm text-ash">{b.summary}</p>
                  <span className="shrink-0 font-mono text-xs text-fog">{fmtTime(b.event_published_at)}</span>
                </div>
                {b.evidence.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2 pl-7">
                    {b.evidence.map((ev) => (
                      <a
                        key={ev.source_item_id}
                        href={ev.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-full border border-steel px-2.5 py-0.5 text-xs text-silver transition-colors hover:border-cyan hover:text-cyan"
                      >
                        {ev.source_name} ↗
                      </a>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function TopicCard({ topic: t, expanded, onToggle }: { topic: Topic; expanded: boolean; onToggle: () => void }) {
  const accent = ACCENTS[(t.order_index - 1) % ACCENTS.length];
  const label = t.credibility_label ? LABEL[t.credibility_label] : null;

  return (
    <article className={`relative overflow-hidden rounded-card border ${expanded ? accent.ring + " " + accent.wash : "border-steel bg-graphite"} transition-colors`}>
      <button onClick={onToggle} className="block w-full px-6 py-5 text-left md:px-8">
        <div className="flex items-center gap-4">
          <span className={`font-serif text-3xl leading-none ${accent.num}`}>
            {String(t.order_index).padStart(2, "0")}
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="truncate font-serif text-lg text-cloud md:text-xl">{t.title}</h3>
            <div className="mt-1.5 flex flex-wrap items-center gap-3">
              {label && <span className={`rounded-full border px-2 py-0.5 text-xs ${label.cls}`}>{label.text}</span>}
              <span className="font-mono text-xs text-fog">{fmtTime(t.event_published_at)}</span>
            </div>
          </div>
          <span className="shrink-0 font-mono text-xs text-fog">{expanded ? "收起" : "展开"}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-steel px-6 pb-8 pt-6 md:px-8">
          <div className="grid gap-x-10 gap-y-5 text-sm md:grid-cols-2">
            <Field label="发生了什么">{t.what_happened}</Field>
            <Field label="为什么现在值得关注">{t.why_now}</Field>
            <Field label="切入角度">{t.angle}</Field>
            <Field label="前三秒钩子" accent>{t.hook}</Field>
            <Field label="结构建议">{t.structure}</Field>
            <Field label="画面建议">{t.visual}</Field>
          </div>

          <div className={`mt-6 rounded-card border p-4 ${accent.box}`}>
            <span className={`font-mono text-xs uppercase tracking-widest ${accent.boxText}`}>建议发布时机</span>
            <p className="mt-1.5 text-sm text-silver">{t.time_window}</p>
          </div>

          <div className="mt-5 text-sm text-fog">
            <span className="font-mono text-xs uppercase tracking-widest">证据</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {t.evidence.length === 0 && <span>—</span>}
              {t.evidence.map((ev) => (
                <a
                  key={ev.source_item_id}
                  href={ev.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`rounded-full border px-3 py-1 text-xs transition-colors hover:border-current ${accent.chip}`}
                >
                  {ev.source_name} · {fmtTime(ev.published_at)}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </article>
  );
}

function Field({ label, children, accent = false }: { label: string; children: string; accent?: boolean }) {
  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-widest text-fog">{label}</p>
      <p className={`mt-1.5 leading-relaxed ${accent ? "text-cyan" : "text-silver"}`}>{children}</p>
    </div>
  );
}
