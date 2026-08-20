"use client";

import { useCallback, useEffect, useState } from "react";
import {
  addTopicFromEvent,
  approveTopic,
  createInviteCodes,
  editTopic,
  getReview,
  listInviteCodes,
  publishReport,
  rejectTopic,
  type InviteCode,
  type ReviewPayload,
  type ReviewTopic,
} from "@/lib/api";
import { fmtTime } from "@/lib/format";

const FIELDS: { key: keyof Pick<ReviewTopic, "title" | "what_happened" | "why_now" | "angle" | "hook" | "structure" | "visual" | "time_window">; label: string }[] = [
  { key: "title", label: "标题" },
  { key: "what_happened", label: "发生了什么" },
  { key: "why_now", label: "为什么现在关注" },
  { key: "angle", label: "切入角度" },
  { key: "hook", label: "前三秒钩子" },
  { key: "structure", label: "结构建议" },
  { key: "visual", label: "画面建议" },
  { key: "time_window", label: "建议发布时机" },
];

export default function ReviewPage() {
  const [data, setData] = useState<ReviewPayload | null>(null);
  const [codes, setCodes] = useState<InviteCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setData(await getReview());
      setCodes(await listInviteCodes());
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "操作失败");
    } finally {
      setBusy(false);
    }
  }

  async function onPublish() {
    setError(null);
    try {
      await publishReport();
      alert("已发布 ✓");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "发布失败");
    }
  }

  return (
    <div className="mx-auto max-w-[880px]">
      <div className="flex flex-wrap items-end justify-between border-b border-steel pb-8 pt-10">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-fog">Review</p>
          <h1 className="mt-3 font-serif text-2xl text-cloud">轻量质检</h1>
          {data?.report_date && (
            <p className="mt-2 font-mono text-xs text-fog">
              {data.report_date} · {data.status === "published" ? "已发布" : "草稿"}
              {data.published_at ? ` · ${fmtTime(data.published_at)} 发布` : ""}
            </p>
          )}
        </div>
        <button
          onClick={onPublish}
          className="mt-4 rounded-full bg-cyan px-6 py-2.5 text-sm font-medium text-obsidian transition-opacity hover:opacity-90"
        >
          发布日报
        </button>
      </div>

      {error && <p className="mt-6 rounded-card border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">{error}</p>}
      {loading && <p className="mt-8 text-fog">加载中…</p>}

      {!loading && data && (
        <>
          {/* 主选题 */}
          <section className="mt-8">
            <h2 className="font-mono text-xs uppercase tracking-widest text-cyan">
              今日选题 · {data.topics.length}
            </h2>
            {data.topics.length === 0 && <p className="mt-3 text-sm text-fog">暂无选题，从下方候选事件补充。</p>}
            <div className="mt-4 space-y-4">
              {data.topics.map((t) => (
                <TopicRow key={t.id} topic={t} editing={editing === t.id} busy={busy}
                  onEdit={() => setEditing(editing === t.id ? null : t.id)}
                  onApprove={() => act(() => approveTopic(t.id))}
                  onReject={() => act(() => rejectTopic(t.id))}
                  onSave={async (fields) => { await editTopic(t.id, fields); setEditing(null); await load(); }}
                />
              ))}
            </div>
          </section>

          {/* 候选事件 */}
          <section className="mt-10">
            <h2 className="font-mono text-xs uppercase tracking-widest text-cyan">
              候选事件 · {data.candidates.length}
            </h2>
            <ul className="mt-4 divide-y divide-steel rounded-card border border-steel bg-graphite px-6">
              {data.candidates.map((c) => (
                <li key={c.id} className="flex items-center gap-3 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm text-ash">{c.title}</p>
                    <p className="font-mono text-xs text-fog">{c.credibility_label} · 证据 {c.evidence_count} · 分 {c.sort_score}</p>
                  </div>
                  <button
                    onClick={() => act(() => addTopicFromEvent(c.id))}
                    disabled={busy}
                    className="shrink-0 rounded-full border border-cyan/40 px-3 py-1 text-xs text-cyan hover:bg-cyan/10 disabled:opacity-50"
                  >
                    补充为选题
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}

      {/* 邀请码 */}
      <section className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="font-mono text-xs uppercase tracking-widest text-cyan">邀请码</h2>
          <button
            onClick={() => act(() => createInviteCodes(5))}
            disabled={busy}
            className="rounded-full border border-cyan/40 px-4 py-1.5 text-xs text-cyan hover:bg-cyan/10 disabled:opacity-50"
          >
            批量生成 5 个
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {codes.slice(0, 10).map((c) => (
            <span key={c.id} className={`rounded-full border px-3 py-1 font-mono text-xs ${c.used ? "border-steel text-fog line-through" : "border-cyan/30 text-cyan"}`}>
              {c.code}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}

function TopicRow({ topic: t, editing, busy, onEdit, onApprove, onReject, onSave }: {
  topic: ReviewTopic;
  editing: boolean;
  busy: boolean;
  onEdit: () => void;
  onApprove: () => void;
  onReject: () => void;
  onSave: (fields: Record<string, string>) => Promise<void>;
}) {
  const [form, setForm] = useState<Record<string, string>>({
    title: t.title, what_happened: t.what_happened, why_now: t.why_now, angle: t.angle,
    hook: t.hook, structure: t.structure, visual: t.visual, time_window: t.time_window,
  });

  return (
    <article className={`rounded-card border p-5 ${t.reviewed ? "border-emerald-500/30 bg-emerald-500/[0.04]" : "border-steel bg-graphite"}`}>
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-serif text-xl text-iris">{String(t.order_index).padStart(2, "0")}</span>
            <span className={`font-mono text-xs ${t.reviewed ? "text-emerald-400" : "text-amber-400"}`}>
              {t.reviewed ? "已通过" : "未质检"}
            </span>
            {t.credibility_label && <span className="font-mono text-xs text-cyan">{t.credibility_label}</span>}
          </div>
          <h3 className="mt-2 font-serif text-lg text-cloud">{t.title}</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {t.evidence.map((ev) => (
              <a key={ev.source_item_id} href={ev.url} target="_blank" rel="noopener noreferrer"
                className="rounded-full border border-steel px-2 py-0.5 text-xs text-silver hover:border-cyan hover:text-cyan">
                {ev.source_name} ↗
              </a>
            ))}
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          {!t.reviewed && (
            <button onClick={onApprove} disabled={busy} className="rounded-full bg-emerald-600 px-3 py-1.5 text-xs text-white hover:opacity-90 disabled:opacity-50">
              通过
            </button>
          )}
          <button onClick={onEdit} className="rounded-full border border-steel px-3 py-1.5 text-xs text-silver hover:border-cyan hover:text-cyan">
            编辑
          </button>
          <button onClick={onReject} disabled={busy} className="rounded-full border border-red-500/40 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-50">
            拒绝
          </button>
        </div>
      </div>

      {editing && (
        <div className="mt-4 space-y-3 border-t border-steel pt-4">
          {FIELDS.map((f) => (
            <label key={f.key} className="block">
              <span className="font-mono text-xs uppercase tracking-widest text-fog">{f.label}</span>
              <textarea
                rows={2}
                value={form[f.key]}
                onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                className="input mt-1 resize-none"
              />
            </label>
          ))}
          <div className="flex gap-2">
            <button onClick={() => onSave(form)} className="rounded-full bg-cyan px-5 py-1.5 text-xs font-medium text-obsidian hover:opacity-90">
              保存修改
            </button>
            <button onClick={onEdit} className="rounded-full border border-steel px-5 py-1.5 text-xs text-silver">
              取消
            </button>
          </div>
        </div>
      )}
    </article>
  );
}
