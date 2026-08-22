"use client";

import { useCallback, useEffect, useState } from "react";
import {
  addTopicFromEvent,
  approveTopic,
  editTopic,
  getReview,
  publishReport,
  removeTopic,
  republishTopic,
  unpublishReport,
  unpublishTopic,
  type ReviewPayload,
  type ReviewTopic,
} from "@/lib/api";
import { fmtTime } from "@/lib/format";

const FIELDS: { key: keyof Pick<ReviewTopic, "title" | "what_happened" | "why_now" | "angle" | "hook" | "structure" | "visual" | "time_window">; label: string }[] = [
  { key: "title", label: "标题" }, { key: "what_happened", label: "发生了什么" },
  { key: "why_now", label: "为什么现在关注" }, { key: "angle", label: "切入角度" },
  { key: "hook", label: "前三秒钩子" }, { key: "structure", label: "结构建议" },
  { key: "visual", label: "画面建议" }, { key: "time_window", label: "建议发布时机" },
];

type WithdrawalConfirmation =
  | { kind: "report" }
  | { kind: "topic"; topic: ReviewTopic }
  | { kind: "topic_republish"; topic: ReviewTopic };

export default function DailyReviewPanel() {
  const [data, setData] = useState<ReviewPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmation, setConfirmation] = useState<WithdrawalConfirmation | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await getReview());
    } catch (e) { setError(e instanceof Error ? e.message : "日报质检加载失败"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function act(fn: () => Promise<unknown>): Promise<boolean> {
    setBusy(true); setError(null);
    try { await fn(); await load(); return true; }
    catch (e) { setError(e instanceof Error ? e.message : "操作失败"); return false; }
    finally { setBusy(false); }
  }

  async function confirmWithdrawal() {
    if (!confirmation) return;
    const action = confirmation.kind === "report"
      ? unpublishReport
      : confirmation.kind === "topic"
        ? () => unpublishTopic(confirmation.topic.id)
        : () => republishTopic(confirmation.topic.id);
    const succeeded = await act(action);
    if (succeeded) {
      setConfirmation(null);
      setEditing(null);
    }
  }

  const isPublished = data?.status === "published";
  const publishedTopicCount = data?.topics.filter((topic) => topic.is_published).length ?? 0;

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Public Daily Review</p>
          <h2 className="mt-2 font-serif text-2xl text-cloud">日报发布</h2>
          {data?.report_date && <p className="mt-2 font-mono text-xs text-fog">{data.report_date} · {data.status === "published" ? "已发布" : "草稿"}{data.published_at ? ` · ${fmtTime(data.published_at)} 发布` : ""}</p>}
        </div>
        <div className="flex flex-wrap gap-2 self-start">
          <button onClick={() => act(publishReport)} disabled={busy || isPublished} className="rounded-full bg-cyan px-6 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-45">
            {isPublished ? "今日已发布" : "发布日报"}
          </button>
          {isPublished && <button onClick={() => setConfirmation({ kind: "report" })} disabled={busy} className="rounded-full border border-red-200 px-5 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-45">下架日报</button>}
        </div>
      </div>

      {error && <p className="mt-5 rounded-card border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading && <p className="mt-8 text-sm text-fog">加载中…</p>}

      {!loading && data && (
        <>
          <div className="mt-8 flex items-center gap-4"><h3 className="eyebrow shrink-0">{isPublished ? `已上架主题 · ${publishedTopicCount}/${data.topics.length}` : `今日主选题 · ${data.topics.length}`}</h3><span className="section-rule" /></div>
          <div className="mt-5 space-y-4">
            {data.topics.map((topic) => (
              <TopicRow
                key={topic.id} topic={topic} editing={editing === topic.id} busy={busy} reportPublished={isPublished}
                onEdit={() => setEditing(editing === topic.id ? null : topic.id)}
                onApprove={() => act(() => approveTopic(topic.id))}
                onRemove={() => act(() => removeTopic(topic.id))}
                onUnpublish={() => setConfirmation({ kind: "topic", topic })}
                onRepublish={() => setConfirmation({ kind: "topic_republish", topic })}
                onSave={async (fields) => { await act(async () => { await editTopic(topic.id, fields); setEditing(null); }); }}
              />
            ))}
            {!data.topics.length && <div className="paper-card rounded-card p-8 text-center text-sm text-fog">暂无选题，可从候选事件补充。</div>}
          </div>

          <div className="mt-10 flex items-center gap-4"><h3 className="eyebrow shrink-0">候选事件 · {data.candidates.length}</h3><span className="section-rule" /></div>
          <ul className="paper-card mt-5 divide-y divide-steel rounded-card px-5">
            {data.candidates.map((candidate) => (
              <li key={candidate.id} className="flex items-center gap-4 py-4">
                <div className="min-w-0 flex-1"><p className="truncate text-sm text-ash">{candidate.title}</p><p className="mt-1 font-mono text-[10px] text-fog">{candidate.credibility_label} · 证据 {candidate.evidence_count} · 分 {candidate.sort_score}</p></div>
                <button onClick={() => act(() => addTopicFromEvent(candidate.id))} disabled={busy || isPublished} title={isPublished ? "请先下架日报" : undefined} className="shrink-0 rounded-full border border-cyan/30 px-3 py-1.5 text-xs text-cyan hover:bg-pale-iris/50 disabled:opacity-45">补充为选题</button>
              </li>
            ))}
          </ul>
        </>
      )}

      {confirmation && (
        <WithdrawalDialog
          confirmation={confirmation}
          busy={busy}
          onConfirm={confirmWithdrawal}
          onClose={() => setConfirmation(null)}
        />
      )}
    </section>
  );
}

function TopicRow({ topic, editing, busy, reportPublished, onEdit, onApprove, onRemove, onUnpublish, onRepublish, onSave }: {
  topic: ReviewTopic; editing: boolean; busy: boolean; reportPublished: boolean; onEdit: () => void; onApprove: () => void;
  onRemove: () => void; onUnpublish: () => void; onRepublish: () => void; onSave: (fields: Record<string, string>) => Promise<void>;
}) {
  const [form, setForm] = useState<Record<string, string>>({
    title: topic.title, what_happened: topic.what_happened, why_now: topic.why_now, angle: topic.angle,
    hook: topic.hook, structure: topic.structure, visual: topic.visual, time_window: topic.time_window,
  });

  const topicStatus = reportPublished
    ? (topic.is_published
        ? `已上架 · ${topic.reviewed ? "已复核" : "待复核"}`
        : `已下架 · ${topic.reviewed ? "已复核" : "待复核"}`)
    : (topic.reviewed ? "已通过" : "未质检");
  const active = topic.reviewed && (!reportPublished || topic.is_published);

  return (
    <article className={`rounded-card border p-5 shadow-sm ${active ? "border-emerald-200 bg-emerald-50/45" : "border-steel bg-white/90"}`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2"><span className="font-serif text-2xl text-iris">{String(topic.order_index).padStart(2, "0")}</span><span className={`font-mono text-[10px] ${active ? "text-emerald-700" : "text-amber-700"}`}>{topicStatus}</span></div>
          <h4 className="mt-2 font-serif text-lg text-cloud">{topic.title}</h4>
          <div className="mt-3 flex flex-wrap gap-2">{topic.evidence.map((item) => <a key={item.source_item_id} href={item.url} target="_blank" rel="noopener noreferrer" className="rounded-full border border-steel px-2.5 py-1 text-xs text-fog hover:border-cyan hover:text-cyan">{item.source_name} ↗</a>)}</div>
        </div>
        <div className="flex shrink-0 gap-2">
          {reportPublished ? <>
            {topic.is_published
              ? <>
                {!topic.reviewed && <button onClick={onApprove} disabled={busy} className="rounded-full bg-emerald-600 px-3 py-1.5 text-xs text-white disabled:opacity-45">通过复核</button>}
                <button onClick={onUnpublish} disabled={busy} className="rounded-full border border-red-200 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 disabled:opacity-45">下架主题</button>
              </>
              : <>
                {!topic.reviewed
                  ? <button onClick={onApprove} disabled={busy} className="rounded-full bg-emerald-600 px-3 py-1.5 text-xs text-white disabled:opacity-45">通过复核</button>
                  : <button onClick={onRepublish} disabled={busy} className="rounded-full bg-cyan px-3 py-1.5 text-xs text-white hover:opacity-90 disabled:opacity-45">重新上架</button>}
                <button onClick={onEdit} disabled={busy} className="rounded-full border border-steel px-3 py-1.5 text-xs text-fog hover:border-cyan hover:text-cyan disabled:opacity-45">编辑</button>
              </>}
          </> : <>
            {!topic.reviewed && <button onClick={onApprove} disabled={busy} className="rounded-full bg-emerald-600 px-3 py-1.5 text-xs text-white disabled:opacity-45">通过</button>}
            <button onClick={onEdit} className="rounded-full border border-steel px-3 py-1.5 text-xs text-fog hover:border-cyan hover:text-cyan">编辑</button>
            <button onClick={onRemove} disabled={busy} className="rounded-full border border-red-200 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50 disabled:opacity-45">移除主题</button>
          </>}
        </div>
      </div>

      {editing && (
        <div className="mt-5 grid gap-4 border-t border-steel pt-5 md:grid-cols-2">
          {FIELDS.map((field) => <label key={field.key} className="block"><span className="font-mono text-[10px] uppercase tracking-widest text-fog">{field.label}</span><textarea rows={3} value={form[field.key]} onChange={(e) => setForm({ ...form, [field.key]: e.target.value })} className="input mt-1.5 resize-y" /></label>)}
          <div className="flex gap-2 md:col-span-2"><button onClick={() => onSave(form)} disabled={busy} className="rounded-full bg-cyan px-5 py-2 text-xs text-white disabled:opacity-45">{busy ? "保存中…" : "保存修改"}</button><button onClick={onEdit} disabled={busy} className="rounded-full border border-steel px-5 py-2 text-xs text-fog disabled:opacity-45">取消</button></div>
        </div>
      )}
    </article>
  );
}

function WithdrawalDialog({ confirmation, busy, onConfirm, onClose }: {
  confirmation: WithdrawalConfirmation;
  busy: boolean;
  onConfirm: () => Promise<void>;
  onClose: () => void;
}) {
  const isReport = confirmation.kind === "report";
  const isRepublish = confirmation.kind === "topic_republish";
  const title = isReport ? "确认下架整份日报？" : isRepublish ? "确认重新上架这个主题？" : "确认下架这个主题？";
  const topicTitle = confirmation.kind !== "report" ? confirmation.topic.title : "";
  const detail = isReport
    ? "公开首页将回退到上一期；若没有上一期，则暂不展示日报。本期内容会保留为草稿。"
    : isRepublish
      ? `“${topicTitle}”已通过复核，确认后将立即恢复到公开日报中。`
      : `“${topicTitle}”将立即从公开日报中撤下，其他主题和整份日报仍保持公开，该主题记录会继续保留。`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-cloud/45 p-4 backdrop-blur-sm" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onClose(); }}>
      <div role="dialog" aria-modal="true" aria-labelledby="withdrawal-title" className="w-full max-w-lg rounded-card border border-steel bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div><p className="eyebrow">{isRepublish ? "Confirm Publication" : "Confirm Withdrawal"}</p><h3 id="withdrawal-title" className="mt-2 font-serif text-2xl text-cloud">{title}</h3></div>
          <button onClick={onClose} disabled={busy} aria-label="关闭确认窗口" className="text-2xl leading-none text-fog hover:text-cloud disabled:opacity-45">×</button>
        </div>
        <p className="mt-4 text-sm leading-7 text-ash">{detail}</p>
        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onClose} disabled={busy} className="rounded-full border border-steel px-5 py-2.5 text-sm text-fog hover:text-cloud disabled:opacity-45">取消</button>
          <button onClick={onConfirm} disabled={busy} className={`rounded-full px-5 py-2.5 text-sm font-medium text-white disabled:opacity-45 ${isRepublish ? "bg-cyan hover:opacity-90" : "bg-red-600 hover:bg-red-700"}`}>{busy ? (isRepublish ? "上架中…" : "下架中…") : isRepublish ? "确认重新上架" : (isReport ? "确认下架日报" : "确认下架主题")}</button>
        </div>
      </div>
    </div>
  );
}
