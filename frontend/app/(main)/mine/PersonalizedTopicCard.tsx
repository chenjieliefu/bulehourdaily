"use client";

import { useState } from "react";
import {
  generatePlan,
  getJob,
  getPlan,
  submitFeedback,
  type Feedback,
  type PersonalizedTopic,
  type Plan,
} from "@/lib/api";
import { fmtTime } from "@/lib/format";

const LABEL: Record<string, string> = {
  official: "官方确认",
  multi_source: "多方报道",
  early_signal: "早期信号",
};

const FB_OPTIONS: { key: Feedback["status"]; label: string }[] = [
  { key: "want", label: "想做" },
  { key: "not_interested", label: "不感兴趣" },
  { key: "published", label: "已发布" },
];

export default function PersonalizedTopicCard({ topic: t }: { topic: PersonalizedTopic }) {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [planOpen, setPlanOpen] = useState(false);
  const [planBusy, setPlanBusy] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback["status"] | null>(t.feedback_status);
  const [fbBusy, setFbBusy] = useState(false);

  async function onExpandPlan() {
    if (plan) {
      setPlanOpen((open) => !open);
      return;
    }
    setPlanBusy(true);
    setPlanError(null);
    try {
      let p: Plan | null = null;
      try {
        p = await getPlan(t.id);
      } catch {
        p = null;
      }
      if (!p) {
        const { job_id } = await generatePlan(t.id);
        for (let i = 0; i < 120; i++) {
          const j = await getJob(job_id);
          if (j.status === "success") break;
          if (j.status === "failed") throw new Error(j.error_message || "生成失败");
          await new Promise((r) => setTimeout(r, 1500));
        }
        p = await getPlan(t.id);
      }
      setPlan(p);
      setPlanOpen(true);
    } catch (e) {
      setPlanError(e instanceof Error ? e.message : "生成失败");
    } finally {
      setPlanBusy(false);
    }
  }

  async function onFeedback(status: Feedback["status"]) {
    setFbBusy(true);
    try {
      let url: string | undefined;
      if (status === "published") {
        url = window.prompt("填写抖音作品链接（可选）：") || undefined;
      }
      const f = await submitFeedback(t.id, status, url);
      setFeedback(f.status);
    } catch (e) {
      alert("反馈失败：" + (e instanceof Error ? e.message : ""));
    } finally {
      setFbBusy(false);
    }
  }

  return (
    <article className="rounded-card border border-steel bg-graphite p-6">
      <div className="flex items-center gap-3">
        <span className="font-serif text-2xl text-iris">{String(t.order_index).padStart(2, "0")}</span>
        {t.credibility_label && (
          <span className="font-mono text-xs text-cyan">{LABEL[t.credibility_label] || t.credibility_label}</span>
        )}
        <span className="font-mono text-xs text-fog">{fmtTime(t.event_published_at)}</span>
      </div>
      <h3 className="mt-3 font-serif text-lg text-cloud">{t.title}</h3>

      <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
        <P label="发生了什么">{t.what_happened}</P>
        <P label="为什么现在关注">{t.why_now}</P>
        <P label="切入角度">{t.angle}</P>
        <P label="前三秒钩子" accent>{t.hook}</P>
        <P label="结构建议">{t.structure}</P>
        <P label="画面建议">{t.visual}</P>
      </div>

      <div className="mt-4 rounded-card border border-cyan/30 bg-cyan/10 p-3">
        <p className="font-mono text-xs text-cyan">{t.time_window}</p>
      </div>

      <div className="mt-3 flex items-center gap-2">
        {t.evidence.length > 0 && (
          <>
            <a href={t.evidence[0].url} target="_blank" rel="noopener noreferrer"
              className="rounded-full border border-steel px-2.5 py-0.5 text-xs text-silver hover:border-cyan hover:text-cyan">
              {t.evidence[0].source_name} ↗
            </a>
            {t.evidence.length > 1 && <span className="font-mono text-xs text-fog">+{t.evidence.length - 1} 来源</span>}
          </>
        )}
      </div>

      {/* 创作方案 */}
      <div className="mt-5 border-t border-steel pt-4">
        <button
          onClick={onExpandPlan}
          disabled={planBusy}
          aria-expanded={planOpen}
          className="inline-flex items-center gap-2 rounded-full border border-cyan/45 bg-pale-iris/60 px-5 py-2 text-xs font-medium text-deep-iris shadow-sm transition-all hover:border-cyan hover:bg-pale-iris disabled:opacity-50"
        >
          {planBusy ? "生成方案中…" : planOpen ? "收起创作方案" : "展开创作方案"}
          {!planBusy && <span aria-hidden="true" className="text-cyan">{planOpen ? "↑" : "↓"}</span>}
        </button>
        {planError && <p className="mt-2 text-xs text-red-400">{planError}</p>}

        {plan && planOpen && (
          <div className="mt-4 space-y-4 rounded-card border border-iris/25 bg-abyss/35 p-5 text-sm">
            <P label="核心观点">{plan.core_viewpoint}</P>
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-fog">开场钩子</p>
              <ul className="mt-1.5 list-inside list-disc space-y-1 text-silver">
                {plan.hooks.map((h, i) => <li key={i}>{h}</li>)}
              </ul>
            </div>
            <P label="结构建议">{plan.structure}</P>
            <P label="画面建议">{plan.visual}</P>
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-fog">标题方向</p>
              <ul className="mt-1.5 list-inside list-disc space-y-1 text-silver">
                {plan.titles.map((x, i) => <li key={i}>{x}</li>)}
              </ul>
            </div>
            <div className="rounded-card border border-amber-200 bg-amber-50/90 p-4">
              <p className="font-mono text-xs uppercase tracking-widest text-amber-700">风险提示</p>
              <p className="mt-1.5 leading-relaxed text-amber-900">{plan.risks}</p>
            </div>
          </div>
        )}
      </div>

      {/* 发布反馈 */}
      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span className="mr-1 font-mono text-xs uppercase tracking-widest text-deep-iris">发布反馈</span>
        {FB_OPTIONS.map((o) => (
          <button
            key={o.key}
            onClick={() => onFeedback(o.key)}
            disabled={fbBusy}
            className={`rounded-full border px-3 py-1 text-xs transition-colors disabled:opacity-50 ${
              feedback === o.key
                ? "border-cyan bg-cyan text-white shadow-sm"
                : "border-steel bg-white text-ash hover:border-cyan hover:bg-pale-iris/50 hover:text-deep-iris"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </article>
  );
}

function P({ label, children, accent = false }: { label: string; children: string; accent?: boolean }) {
  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-widest text-fog">{label}</p>
      <p className={`mt-1 leading-relaxed ${accent ? "text-cyan" : "text-silver"}`}>{children}</p>
    </div>
  );
}
