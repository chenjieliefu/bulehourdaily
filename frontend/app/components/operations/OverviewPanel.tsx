"use client";

import { useCallback, useEffect, useState } from "react";
import { getOperationsOverview, type OperationsOverview } from "@/lib/api";

type WorkspaceTab = "overview" | "daily" | "creators" | "personalized" | "feedback";

export default function OverviewPanel({ onOpen }: { onOpen: (tab: WorkspaceTab) => void }) {
  const [data, setData] = useState<OperationsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await getOperationsOverview());
    } catch (e) {
      setError(e instanceof Error ? e.message : "运营数据加载失败");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <LoadingState />;

  const missingPersonalized = Math.max(0, data.today_personalized_expected - data.today_personalized_reports);
  const tasks = [
    data.public_report_status !== "published"
      ? { label: data.public_report_status ? `公共日报还有 ${data.unreviewed_topics} 个选题待质检` : "今日公共日报尚未生成", tab: "daily" as const, tone: "amber" }
      : null,
    missingPersonalized > 0
      ? { label: `${missingPersonalized} 位有资格的创作者尚未收到今日个性化日报`, tab: "personalized" as const, tone: "amber" }
      : null,
    data.failed_mail_deliveries > 0
      ? { label: `${data.failed_mail_deliveries} 封个性化日报邮件发送失败`, tab: "personalized" as const, tone: "red" }
      : null,
    data.new_product_feedback > 0
      ? { label: `${data.new_product_feedback} 条新产品反馈等待处理`, tab: "feedback" as const, tone: "blue" }
      : null,
    data.expiring_subscribers > 0
      ? { label: `${data.expiring_subscribers} 位订阅用户将在 7 天内到期`, tab: "creators" as const, tone: "blue" }
      : null,
  ].filter(Boolean) as Array<{ label: string; tab: WorkspaceTab; tone: string }>;

  const metrics = [
    ["注册创作者", data.creators_total, `${data.profiles_completed} 人已完成画像`],
    ["有效订阅", data.active_subscribers, `${data.expiring_subscribers} 人 7 天内到期`],
    ["体验中", data.trial_creators, `${data.trial_exhausted} 人已无个性化资格`],
    ["今日个性化日报", `${data.today_personalized_reports}/${data.today_personalized_expected}`, missingPersonalized ? `${missingPersonalized} 人待生成` : "当前应发已完成"],
    ["邮件失败", data.failed_mail_deliveries, "仅统计今天"],
    ["新产品反馈", data.new_product_feedback, "等待运营处理"],
  ];

  return (
    <div className="space-y-8">
      <section>
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Today · {data.report_date}</p>
            <h2 className="mt-2 font-serif text-2xl text-cloud">今天先处理这些</h2>
          </div>
          <button onClick={load} className="rounded-full border border-steel px-4 py-2 text-xs text-fog hover:border-cyan hover:text-cyan">
            刷新数据
          </button>
        </div>

        {tasks.length ? (
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {tasks.map((task) => (
              <button
                key={task.label}
                onClick={() => onOpen(task.tab)}
                className={`flex items-center justify-between rounded-card border bg-white/85 px-5 py-4 text-left text-sm shadow-sm transition-all hover:-translate-y-0.5 ${
                  task.tone === "red" ? "border-red-200 text-red-700" : task.tone === "amber" ? "border-amber-200 text-amber-800" : "border-cyan/20 text-cloud"
                }`}
              >
                <span>{task.label}</span><span aria-hidden="true">→</span>
              </button>
            ))}
          </div>
        ) : (
          <div className="mt-5 rounded-card border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
            当前没有待处理异常，今日运营链路正常。
          </div>
        )}
      </section>

      <section>
        <div className="flex items-center gap-4">
          <h2 className="eyebrow shrink-0">运营状态</h2><span className="section-rule" />
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {metrics.map(([label, value, note]) => (
            <div key={String(label)} className="paper-card rounded-card p-5">
              <p className="font-mono text-[10px] uppercase tracking-widest text-fog">{label}</p>
              <p className="mt-3 font-serif text-3xl text-cloud">{value}</p>
              <p className="mt-2 text-xs text-fog">{note}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-feature border border-steel bg-abyss/45 p-6">
        <p className="eyebrow">数据口径</p>
        <p className="mt-3 text-sm leading-7 text-fog">
          “最近互动”只来自个性化日报生成、创作方案展开和发布反馈。当前尚未采集登录时间、日报打开和邮件打开，因此不把这些数据称为用户活跃度。
        </p>
      </section>
    </div>
  );
}

function LoadingState() {
  return <div className="paper-card rounded-feature p-10 text-center text-sm text-fog">正在汇总本地运营数据…</div>;
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-card border border-red-200 bg-red-50 p-6 text-sm text-red-700">
      <p>{message}</p>
      <button onClick={onRetry} className="mt-3 rounded-full border border-red-300 px-4 py-1.5 text-xs">重试</button>
    </div>
  );
}
