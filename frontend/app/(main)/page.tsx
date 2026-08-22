"use client";

import { useEffect, useState } from "react";
import { getLatestReport, type Report } from "@/lib/api";
import ReportView from "@/app/components/ReportView";

export default function DailyPage() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setReport(await getLatestReport());
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-[1180px]">
      <header className="flex flex-col gap-4 border-b border-steel/80 pb-6 pt-8 sm:flex-row sm:items-end sm:justify-between lg:pt-10">
        <div>
          <p className="eyebrow">Public Daily · 08:00</p>
          <h1 className="mt-2 font-serif text-3xl text-cloud md:text-4xl">公开日报</h1>
        </div>
        <p className="max-w-md text-sm leading-relaxed text-fog sm:text-right">
          从全球 AI 动态中筛出真正值得关注的变化，<br className="hidden md:block" />每天给你三个可以立即开拍的选题。
        </p>
      </header>

      {loading && (
        <div className="paper-card mt-8 rounded-feature p-10 text-center">
          <span className="mx-auto block h-2 w-24 animate-pulse rounded-full bg-periwinkle/40" />
          <p className="mt-4 text-sm text-fog">正在加载今日日报…</p>
        </div>
      )}

      {!loading && error && (
        <div className="mt-8 rounded-card border border-red-200 bg-red-50 p-6 text-center shadow-sm">
          <p className="text-red-700">加载失败：{error}</p>
          <p className="mt-2 text-sm text-fog">请确认后端服务已启动。</p>
        </div>
      )}

      {!loading && !error && !report && (
        <div className="paper-card mt-8 rounded-feature p-10 text-center">
          <span className="mx-auto block h-12 w-12 rounded-full bg-pale-iris" />
          <p className="text-silver">今日日报尚未生成。</p>
          <p className="mt-2 text-sm text-fog">每天北京时间 08:00 自动生成。</p>
        </div>
      )}

      {!loading && !error && report && <ReportView report={report} />}
    </div>
  );
}
