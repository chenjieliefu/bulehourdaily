"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getCollectionStatus, getReview, type CollectionStatus, type ReviewPayload } from "@/lib/api";
import { fmtTime } from "@/lib/format";

type PipelineData = {
  collection: CollectionStatus;
  review: ReviewPayload;
};

export default function TodayPipelinePanel({ refreshKey = 0 }: { refreshKey?: number }) {
  const [data, setData] = useState<PipelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [collection, review] = await Promise.all([getCollectionStatus(), getReview()]);
      setData({ collection, review });
    } catch (e) {
      setError(e instanceof Error ? e.message : "今日流程加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load, refreshKey]);

  const failedSources = useMemo(
    () => data?.collection.sources.filter((source) => source.enabled && source.last_status === "failed") ?? [],
    [data],
  );

  if (loading) return <div className="paper-card rounded-card p-8 text-center text-sm text-fog">正在汇总今日流程…</div>;
  if (error || !data) return <div className="rounded-card border border-red-200 bg-red-50 p-5 text-sm text-red-700"><p>{error || "今日流程不可用"}</p><button onClick={load} className="mt-3 rounded-full border border-red-300 px-4 py-1.5 text-xs">重新加载</button></div>;

  const reviewedCount = data.review.topics.filter((topic) => topic.reviewed).length;
  const candidateCount = data.review.candidates.length;
  const steps = [
    {
      label: "信息采集",
      value: data.collection.last_collect_at ? "已运行" : "待运行",
      note: data.collection.last_collect_at ? fmtTime(data.collection.last_collect_at) : "尚无采集记录",
      done: Boolean(data.collection.last_collect_at),
    },
    {
      label: "候选事件",
      value: `${candidateCount} 条`,
      note: "可补充进今日选题",
      done: candidateCount > 0 || data.review.topics.length > 0,
    },
    {
      label: "主选题",
      value: `${data.review.topics.length}/3`,
      note: data.review.topics.length === 3 ? "数量已满足" : "还需调整",
      done: data.review.topics.length === 3,
    },
    {
      label: "人工质检",
      value: `${reviewedCount}/${data.review.topics.length}`,
      note: reviewedCount === data.review.topics.length && reviewedCount > 0 ? "全部通过" : "仍有待确认",
      done: reviewedCount === data.review.topics.length && reviewedCount > 0,
    },
    {
      label: "正式发布",
      value: data.review.status === "published" ? "已发布" : data.review.status === "draft" ? "草稿" : "未生成",
      note: data.review.published_at ? fmtTime(data.review.published_at) : "等待人工发布",
      done: data.review.status === "published",
    },
  ];

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Today · {data.review.report_date || "尚未生成"}</p>
          <h2 className="mt-2 font-serif text-2xl text-cloud">今日进度</h2>
          <p className="mt-2 text-sm text-fog">按顺序看完五步，就知道今天还剩什么。</p>
        </div>
        <button onClick={load} className="self-start rounded-full border border-steel bg-white px-4 py-2 text-xs text-fog hover:border-cyan hover:text-cyan">刷新状态</button>
      </div>

      <div className="mt-6 grid overflow-hidden rounded-card border border-steel bg-white shadow-sm sm:grid-cols-2 xl:grid-cols-5">
        {steps.map((step, index) => (
          <div key={step.label} className="relative min-h-36 border-b border-steel p-5 last:border-b-0 sm:[&:nth-child(odd)]:border-r xl:border-b-0 xl:border-r xl:last:border-r-0">
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono text-[10px] tracking-widest text-fog">STEP {String(index + 1).padStart(2, "0")}</span>
              <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${step.done ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{step.done ? "✓" : "·"}</span>
            </div>
            <p className="mt-5 text-sm text-fog">{step.label}</p>
            <p className="mt-1 font-serif text-xl text-cloud">{step.value}</p>
            <p className="mt-2 text-[11px] leading-5 text-fog">{step.note}</p>
          </div>
        ))}
      </div>

      <div className={`mt-4 flex flex-col gap-3 rounded-card border px-5 py-4 text-sm sm:flex-row sm:items-center sm:justify-between ${failedSources.length ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"}`}>
        <p>{failedSources.length ? `${failedSources.length} 个启用信息源最近采集失败，需要检查。` : `当前 ${data.collection.enabled_sources} 个启用信息源没有失败告警。`}</p>
        <Link href="/ops/sources" className="shrink-0 text-xs underline underline-offset-4">查看信息源</Link>
      </div>
    </section>
  );
}
