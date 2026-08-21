"use client";

import { useCallback, useEffect, useState } from "react";
import {
  listCreatorOperations,
  listPersonalizedOperations,
  type CreatorOperations,
  type PersonalizedOperationsReport,
  type PersonalizedOperationsTopic,
} from "@/lib/api";

const CREDIBILITY: Record<string, string> = { official: "官方确认", multi_source: "多方报道", early_signal: "早期信号" };
const FEEDBACK: Record<string, string> = { want: "想做", not_interested: "不感兴趣", published: "已发布" };

export default function PersonalizedPanel({ initialUserId }: { initialUserId: number | null }) {
  const [creators, setCreators] = useState<CreatorOperations[]>([]);
  const [reports, setReports] = useState<PersonalizedOperationsReport[]>([]);
  const [userId, setUserId] = useState(initialUserId ? String(initialUserId) : "");
  const [reportDate, setReportDate] = useState("");
  const [openTopic, setOpenTopic] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCreatorOperations().then(setCreators).catch(() => undefined);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setReports(await listPersonalizedOperations({
        userId: userId ? Number(userId) : undefined,
        reportDate: reportDate || undefined,
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "个性化内容加载失败");
    } finally {
      setLoading(false);
    }
  }, [reportDate, userId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  return (
    <section>
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="eyebrow">Personalized Quality</p>
          <h2 className="mt-2 font-serif text-2xl text-cloud">每位创作者实际收到的内容</h2>
          <p className="mt-2 text-sm text-fog">第一版只读，集中核对画像匹配、推荐理由、创作方案和发布反馈。</p>
        </div>
        <button onClick={load} className="self-start rounded-full border border-steel px-4 py-2 text-xs text-fog hover:border-cyan hover:text-cyan">刷新</button>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
        <select value={userId} onChange={(e) => setUserId(e.target.value)} className="input h-11">
          <option value="">全部创作者</option>
          {creators.map((creator) => <option key={creator.id} value={creator.id}>{creator.email}</option>)}
        </select>
        <input type="date" value={reportDate} onChange={(e) => setReportDate(e.target.value)} className="input h-11" />
      </div>

      {error && <p className="mt-5 rounded-card border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading ? <p className="mt-8 text-sm text-fog">加载中…</p> : (
        <div className="mt-6 space-y-5">
          {reports.map((report) => (
            <article key={report.id} className="paper-card overflow-hidden rounded-feature">
              <header className="border-b border-steel bg-abyss/40 px-6 py-5 sm:px-8">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="font-mono text-[10px] uppercase tracking-widest text-fog">{report.report_date} · #{report.id}</p>
                    <h3 className="mt-2 font-serif text-xl text-cloud">{report.email}</h3>
                    <p className="mt-2 text-sm text-silver">{report.summary || "无日报摘要"}</p>
                  </div>
                  <span className={`self-start rounded-full border px-3 py-1 text-xs ${report.mail_status === "failed" ? "border-red-200 bg-red-50 text-red-700" : "border-steel bg-white text-fog"}`}>
                    邮件 {mailLabel(report.mail_status)}
                  </span>
                </div>
                {report.reason && <p className="mt-4 rounded-card border border-cyan/15 bg-white/70 px-4 py-3 text-sm leading-6 text-ash"><span className="text-cyan">整份推荐理由：</span>{report.reason}</p>}
              </header>

              <div className="space-y-3 p-5 sm:p-6">
                {report.topics.map((topic) => (
                  <TopicAuditCard key={topic.id} topic={topic} open={openTopic === topic.id} onToggle={() => setOpenTopic(openTopic === topic.id ? null : topic.id)} />
                ))}
              </div>
            </article>
          ))}
          {!reports.length && <div className="paper-card rounded-feature p-12 text-center text-sm text-fog">当前筛选条件下没有个性化日报。</div>}
        </div>
      )}
    </section>
  );
}

function TopicAuditCard({ topic, open, onToggle }: { topic: PersonalizedOperationsTopic; open: boolean; onToggle: () => void }) {
  return (
    <div className="rounded-card border border-steel bg-white/80">
      <button onClick={onToggle} className="flex w-full items-start gap-4 px-5 py-4 text-left">
        <span className="font-serif text-2xl text-iris">{String(topic.order_index).padStart(2, "0")}</span>
        <span className="min-w-0 flex-1">
          <span className="block font-serif text-lg text-cloud">{topic.title}</span>
          <span className="mt-1.5 flex flex-wrap gap-2 text-xs text-fog">
            {topic.credibility_label && <span>{CREDIBILITY[topic.credibility_label]}</span>}
            <span>· {topic.plan ? "已展开方案" : "未展开方案"}</span>
            <span>· {topic.feedback_status ? FEEDBACK[topic.feedback_status] : "暂无发布反馈"}</span>
          </span>
        </span>
        <span className="font-mono text-[10px] text-fog">{open ? "收起 ↑" : "核对 ↓"}</span>
      </button>

      {open && (
        <div className="border-t border-steel px-5 pb-6 pt-5">
          <div className="rounded-card border border-cyan/20 bg-pale-iris/30 p-4 text-sm leading-6 text-ash">
            <p className="font-mono text-[10px] uppercase tracking-widest text-cyan">为什么推荐给这个账号</p>
            <p className="mt-2">{topic.recommendation_reason || "未生成推荐理由"}</p>
          </div>
          <div className="mt-5 grid gap-5 text-sm md:grid-cols-2">
            <Field label="发生了什么" value={topic.what_happened} /><Field label="为什么现在关注" value={topic.why_now} />
            <Field label="切入角度" value={topic.angle} /><Field label="前三秒钩子" value={topic.hook} />
            <Field label="结构建议" value={topic.structure} /><Field label="画面建议" value={topic.visual} />
          </div>
          <p className="mt-5 text-sm text-cyan">{topic.time_window}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {topic.evidence.map((item) => <a key={item.source_item_id} href={item.url} target="_blank" rel="noopener noreferrer" className="rounded-full border border-steel px-3 py-1 text-xs text-fog hover:border-cyan hover:text-cyan">{item.source_name} ↗</a>)}
          </div>
          {topic.plan && (
            <div className="mt-5 rounded-card border border-iris/20 bg-abyss/35 p-5 text-sm">
              <p className="font-mono text-[10px] uppercase tracking-widest text-deep-iris">已展开的创作方案</p>
              <p className="mt-3 font-medium text-cloud">{topic.plan.core_viewpoint}</p>
              <p className="mt-2 leading-6 text-silver">{topic.plan.structure}</p>
              <p className="mt-3 text-xs text-amber-700">风险：{topic.plan.risks}</p>
            </div>
          )}
          {topic.feedback_status && (
            <div className="mt-5 text-sm text-silver">发布反馈：<span className="text-cyan">{FEEDBACK[topic.feedback_status]}</span>{topic.feedback_douyin_url && <> · <a href={topic.feedback_douyin_url} target="_blank" rel="noopener noreferrer" className="underline">查看作品</a></>}</div>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return <div><p className="font-mono text-[10px] uppercase tracking-widest text-fog">{label}</p><p className="mt-1.5 leading-6 text-silver">{value}</p></div>;
}

function mailLabel(status: string | null) {
  return status === "sent" ? "已发送" : status === "failed" ? "失败" : status === "pending" ? "待发送" : "无记录";
}
