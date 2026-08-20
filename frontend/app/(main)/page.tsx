"use client";

import { useEffect, useState } from "react";
import { getReport, listReports, type Report } from "@/lib/api";
import ReportView from "@/app/components/ReportView";

export default function DailyPage() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const reports = await listReports();
        if (reports.length > 0) setReport(await getReport(reports[0].id));
        else setReport(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-[1040px]">
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

      {!loading && !error && report && (
        <>
          <ReportView report={report} />

          {/* 订阅价值说明 */}
          <section id="subscribe" className="paper-card relative mx-auto mt-16 max-w-[960px] overflow-hidden rounded-feature p-8 md:p-10">
            <div className="pointer-events-none absolute -right-12 -top-16 h-56 w-56 rounded-full bg-pale-iris/70 blur-3xl" />
            <p className="eyebrow relative">为什么订阅</p>
            <h2 className="mt-4 font-serif text-2xl text-cloud">
              通用日报看今天，个性化日报看「适合我的今天」。
            </h2>
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <div className="rounded-card border border-steel bg-white/75 p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-fog">免费 · 通用日报</p>
                <ul className="mt-4 space-y-2 text-sm text-silver">
                  <li>· 每天 3 个通用选题</li>
                  <li>· 5-7 条热点速览</li>
                  <li>· 证据链接与可信度标签</li>
                  <li>· 最近 7 天归档</li>
                </ul>
              </div>
              <div className="rounded-card border border-cyan/20 bg-pale-iris/45 p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-cyan">体验 / 订阅 · 个性化日报</p>
                <ul className="mt-4 space-y-2 text-sm text-silver">
                  <li>· 按你的账号定位，重选 3 个选题</li>
                  <li>· 每个选题可展开创作方案</li>
                  <li>· 每日邮件送达</li>
                  <li>· 发布反馈，越用越懂你</li>
                </ul>
                <button
                  disabled
                  className="mt-6 cursor-not-allowed rounded-full bg-cyan px-6 py-2.5 text-sm font-medium text-white opacity-60"
                >
                  申请体验（即将开放）
                </button>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
