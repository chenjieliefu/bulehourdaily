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
    <div>
      {loading && <p className="mt-16 text-center text-fog">正在加载今日日报…</p>}

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
          <ReportView report={report} />

          {/* 订阅价值说明 */}
          <section id="subscribe" className="mx-auto mt-16 max-w-[880px] rounded-feature border border-steel bg-abyss/40 p-8 md:p-10">
            <p className="font-mono text-xs uppercase tracking-widest text-cyan">为什么订阅</p>
            <h2 className="mt-4 font-serif text-2xl text-cloud">
              通用日报看今天，个性化日报看「适合我的今天」。
            </h2>
            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <div className="rounded-card border border-steel bg-graphite p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-fog">免费 · 通用日报</p>
                <ul className="mt-4 space-y-2 text-sm text-silver">
                  <li>· 每天 3 个通用选题</li>
                  <li>· 5-7 条热点速览</li>
                  <li>· 证据链接与可信度标签</li>
                  <li>· 最近 7 天归档</li>
                </ul>
              </div>
              <div className="rounded-card border border-cyan/30 bg-cyan/[0.06] p-6">
                <p className="font-mono text-xs uppercase tracking-widest text-cyan">体验 / 订阅 · 个性化日报</p>
                <ul className="mt-4 space-y-2 text-sm text-silver">
                  <li>· 按你的账号定位，重选 3 个选题</li>
                  <li>· 每个选题可展开创作方案</li>
                  <li>· 每日邮件送达</li>
                  <li>· 发布反馈，越用越懂你</li>
                </ul>
                <button
                  disabled
                  className="mt-6 cursor-not-allowed rounded-full bg-cyan px-6 py-2.5 text-sm font-medium text-obsidian opacity-60"
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
