"use client";

import { useState } from "react";
import { fmtDate, fmtTime } from "@/lib/format";
import type { Report, Topic } from "@/lib/api";

const LABEL: Record<string, { text: string; cls: string }> = {
  official: { text: "官方确认", cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  multi_source: { text: "多方报道", cls: "bg-sky-50 text-sky-700 border-sky-200" },
  early_signal: { text: "早期信号", cls: "bg-amber-50 text-amber-700 border-amber-200" },
};

const ACCENTS = [
  { num: "text-deep-iris", ring: "border-iris/35", wash: "bg-iris/[0.06]", chip: "border-iris/35 text-deep-iris", box: "border-iris/25 bg-pale-iris/45", boxText: "text-deep-iris", bar: "bg-iris" },
  { num: "text-cyan", ring: "border-cyan/30", wash: "bg-cyan/[0.05]", chip: "border-cyan/30 text-cyan", box: "border-cyan/20 bg-sky-50", boxText: "text-cyan", bar: "bg-cyan" },
  { num: "text-orchid", ring: "border-orchid/35", wash: "bg-orchid/[0.06]", chip: "border-orchid/35 text-amber-700", box: "border-orchid/25 bg-orange-50/70", boxText: "text-amber-700", bar: "bg-orchid" },
];

export default function ReportView({ report }: { report: Report }) {
  const [expandedId, setExpandedId] = useState<number | null>(report.topics[0]?.id ?? null);

  return (
    <div className="mx-auto mt-8 max-w-[960px]">
      {/* 日报头 */}
      <div className="report-cover rounded-feature border border-white/80 px-7 pb-10 pt-10 sm:px-10 sm:pb-12 sm:pt-12">
        <p className="eyebrow text-deep-iris">
          {fmtDate(report.report_date)} · 通用日报
        </p>
        <h2 className="mt-5 max-w-3xl font-serif text-3xl leading-[1.35] text-cloud md:text-[2.6rem]">
          {report.summary || "今日摘要"}
        </h2>
        <p className="mt-6 font-mono text-[11px] text-deep-iris/70">
          生成 {fmtTime(report.updated_at)} · 最近采集 {fmtTime(report.last_collect_at)}
        </p>
      </div>

      {/* 选题列表 */}
      <section className="mt-12">
        <div className="flex items-center gap-4">
          <h2 className="eyebrow shrink-0">今日选题</h2>
          <span className="section-rule" />
          <span className="font-mono text-xs text-fog">{String(report.topics.length).padStart(2, "0")}</span>
        </div>
        <div className="mt-5 grid gap-4">
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
        <section className="mt-14">
          <div className="flex items-center gap-4">
            <h2 className="eyebrow shrink-0">热点速览</h2>
            <span className="section-rule" />
            <span className="font-mono text-xs text-fog">{String(report.briefs.length).padStart(2, "0")}</span>
          </div>
          <ul className="paper-card mt-5 divide-y divide-steel rounded-card px-5 sm:px-7">
            {report.briefs.map((b) => (
              <li key={b.id} className="py-5">
                <div className="flex items-start gap-3 sm:gap-4">
                  <span className="mt-0.5 font-mono text-xs text-deep-iris">{String(b.order_index).padStart(2, "0")}</span>
                  <p className="flex-1 text-sm leading-relaxed text-ash">{b.summary}</p>
                  <span className="hidden shrink-0 font-mono text-xs text-fog sm:block">{fmtTime(b.event_published_at)}</span>
                </div>
                {b.evidence.length > 0 && (
                  <div className="mt-2 flex items-center gap-2 pl-7">
                    <a
                      href={b.evidence[0].url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-full border border-steel bg-abyss/40 px-2.5 py-0.5 text-xs text-silver transition-colors hover:border-cyan hover:text-cyan"
                    >
                      {b.evidence[0].source_name} ↗
                    </a>
                    {b.evidence.length > 1 && (
                      <span className="font-mono text-xs text-fog">+{b.evidence.length - 1} 来源</span>
                    )}
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
    <article className={`relative overflow-hidden rounded-card border shadow-[0_12px_32px_rgba(50,91,116,0.06)] ${expanded ? accent.ring + " " + accent.wash : "border-steel bg-white/90 hover:border-periwinkle/70"} transition-all`}>
      <span className={`absolute inset-y-0 left-0 w-1 ${accent.bar}`} />
      <button onClick={onToggle} className="block w-full px-6 py-6 text-left md:px-8">
        <div className="flex items-center gap-4">
          <span className={`font-serif text-3xl leading-none ${accent.num}`}>
            {String(t.order_index).padStart(2, "0")}
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="font-serif text-lg leading-snug text-cloud md:text-xl">{t.title}</h3>
            <div className="mt-1.5 flex flex-wrap items-center gap-3">
              {label && <span className={`rounded-full border px-2 py-0.5 text-xs ${label.cls}`}>{label.text}</span>}
              <span className="font-mono text-xs text-fog">{fmtTime(t.event_published_at)}</span>
            </div>
          </div>
          <span className="shrink-0 rounded-full border border-steel bg-white/65 px-3 py-1 font-mono text-[10px] text-fog">{expanded ? "收起 ↑" : "展开 ↓"}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-steel/80 bg-white/55 px-6 pb-8 pt-7 md:px-8">
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
            <p className="mt-1.5 text-sm text-ash">{t.time_window}</p>
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
