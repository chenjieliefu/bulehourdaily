"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  generatePersonalized,
  getJob,
  getPersonalizedReport,
  listPersonalizedReports,
  type PersonalizedReport,
  type PersonalizedReportDetail,
} from "@/lib/api";
import { fmtDate, fmtTime } from "@/lib/format";

const LABEL: Record<string, string> = {
  official: "官方确认",
  multi_source: "多方报道",
  early_signal: "早期信号",
};

export default function MinePage() {
  const [reports, setReports] = useState<PersonalizedReport[]>([]);
  const [detail, setDetail] = useState<PersonalizedReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState("");

  const load = useCallback(async () => {
    try {
      const list = await listPersonalizedReports();
      setReports(list);
      if (list.length > 0 && !detail) {
        setDetail(await getPersonalizedReport(list[0].id));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [detail]);

  useEffect(() => {
    // 挂载时拉取一次数据
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function onGenerate() {
    setBusy(true);
    setError(null);
    setProgress("");
    try {
      const { job_id } = await generatePersonalized();
      for (let i = 0; i < 120; i++) {
        const job = await getJob(job_id);
        if (job.status === "success") break;
        if (job.status === "failed") throw new Error(job.error_message || "生成失败");
        setProgress("生成中…");
        await new Promise((r) => setTimeout(r, 1500));
      }
      await load();
      const list = await listPersonalizedReports();
      if (list.length > 0) setDetail(await getPersonalizedReport(list[0].id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "生成失败");
    } finally {
      setBusy(false);
      setProgress("");
    }
  }

  return (
    <div className="mx-auto max-w-[880px]">
      <div className="flex flex-wrap items-end justify-between border-b border-steel pb-8 pt-10">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-fog">My Daily</p>
          <h1 className="mt-3 font-serif text-2xl text-cloud">我的个性化日报</h1>
        </div>
        <div className="mt-4 flex items-center gap-4">
          <span className="font-mono text-xs text-fog">剩余体验 {Math.max(0, 3 - reports.length)} 份</span>
          <button
            onClick={onGenerate}
            disabled={busy}
            className="rounded-full bg-cyan px-6 py-2.5 text-sm font-medium text-obsidian transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {busy ? (progress || "生成中…") : "生成今日个性化日报"}
          </button>
        </div>
      </div>

      {error && <p className="mt-6 rounded-card border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">{error}</p>}

      {loading ? (
        <p className="mt-8 text-fog">加载中…</p>
      ) : reports.length === 0 ? (
        <div className="mt-16 rounded-card border border-steel bg-graphite p-10 text-center">
          <p className="text-silver">还没有个性化日报。</p>
          <p className="mt-2 text-sm text-fog">
            先到 <Link href="/profile" className="text-cyan hover:underline">创作者画像</Link> 填好画像，再点上方按钮生成。
          </p>
        </div>
      ) : (
        <div className="mt-8 grid gap-6 lg:grid-cols-[240px_1fr]">
          {/* 历史列表 */}
          <ul className="space-y-2">
            {reports.map((r) => (
              <li key={r.id}>
                <button
                  onClick={async () => setDetail(await getPersonalizedReport(r.id))}
                  className={`w-full rounded-card border px-4 py-3 text-left transition-colors ${
                    detail?.id === r.id ? "border-cyan/40 bg-cyan/10" : "border-steel bg-graphite hover:border-steel"
                  }`}
                >
                  <p className="font-mono text-xs text-fog">{fmtDate(r.report_date)}</p>
                  <p className="mt-1 truncate text-sm text-ash">{r.summary || "（无摘要）"}</p>
                </button>
              </li>
            ))}
          </ul>

          {/* 详情 */}
          {detail && (
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-fog">
                {fmtDate(detail.report_date)} · 个性化日报
              </p>
              <h2 className="mt-3 font-serif text-xl leading-snug text-cloud">{detail.summary}</h2>
              {detail.reason && (
                <div className="mt-3 rounded-card border border-iris/30 bg-iris/10 p-4">
                  <span className="font-mono text-xs uppercase tracking-widest text-pale-iris">为什么推荐给你</span>
                  <p className="mt-1.5 text-sm text-silver">{detail.reason}</p>
                </div>
              )}

              <div className="mt-6 space-y-4">
                {detail.topics.map((t) => (
                  <article key={t.id} className="rounded-card border border-steel bg-graphite p-6">
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
                          {t.evidence.length > 1 && (
                            <span className="font-mono text-xs text-fog">+{t.evidence.length - 1} 来源</span>
                          )}
                        </>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
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
