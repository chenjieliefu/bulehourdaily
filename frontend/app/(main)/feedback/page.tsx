"use client";

import { useEffect, useState } from "react";
import {
  submitProductFeedback,
  type ProductFeedbackCategory,
  type ProductFeedbackReceipt,
} from "@/lib/api";
import { getUser } from "@/lib/auth";

const CATEGORIES: Array<{ value: ProductFeedbackCategory; label: string }> = [
  { value: "bug", label: "功能问题" },
  { value: "content", label: "内容质量" },
  { value: "experience", label: "使用体验" },
  { value: "membership", label: "会员与付费" },
  { value: "suggestion", label: "功能建议" },
  { value: "other", label: "其他" },
];

export default function FeedbackPage() {
  const [category, setCategory] = useState<ProductFeedbackCategory | "">("");
  const [content, setContent] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<ProductFeedbackReceipt | null>(null);

  useEffect(() => {
    // 登录用户自动带入联系邮箱；访客仍可自行填写或留空。
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setEmail(getUser()?.email ?? "");
  }, []);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!category) {
      setError("请选择问题类型");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const created = await submitProductFeedback({
        category,
        content,
        contact_email: email || undefined,
        page_url: window.location.href,
      });
      setReceipt(created);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败，请稍后重试");
    } finally {
      setBusy(false);
    }
  }

  function resetForm() {
    setCategory("");
    setContent("");
    setError(null);
    setReceipt(null);
  }

  return (
    <div className="mx-auto max-w-[1080px] pb-20">
      <header className="flex flex-col gap-4 border-b border-steel/80 pb-6 pt-8 sm:flex-row sm:items-end sm:justify-between lg:pt-10">
        <div>
          <p className="eyebrow">Feedback</p>
          <h1 className="mt-2 font-serif text-3xl text-cloud md:text-4xl">意见反馈</h1>
        </div>
        <p className="max-w-md text-sm leading-relaxed text-fog sm:text-right">
          告诉我们你遇到的问题，或希望微蓝日报改进的地方。
        </p>
      </header>

      <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <section className="paper-card overflow-hidden rounded-feature">
          {receipt ? (
            <div className="px-7 py-14 text-center sm:px-10">
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-2xl text-emerald-600">✓</span>
              <p className="eyebrow mt-6">Submitted</p>
              <h2 className="mt-3 font-serif text-2xl text-cloud">反馈已收到，谢谢你</h2>
              <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-fog">
                我们已经保存了这条反馈。若需要进一步确认，会通过你留下的邮箱联系。
              </p>
              <p className="mt-3 font-mono text-[10px] text-fog">反馈编号 #{receipt.id}</p>
              <button
                type="button"
                onClick={resetForm}
                className="mt-7 rounded-full border border-cyan/30 bg-pale-iris/45 px-6 py-2.5 text-sm text-cyan transition-colors hover:bg-pale-iris/75"
              >
                再提交一条
              </button>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="p-6 sm:p-8">
              <div>
                <label htmlFor="feedback-category" className="text-sm font-medium text-cloud">问题类型</label>
                <select
                  id="feedback-category"
                  required
                  value={category}
                  onChange={(event) => setCategory(event.target.value as ProductFeedbackCategory | "")}
                  className="input mt-2 h-12"
                >
                  <option value="">请选择问题类型</option>
                  {CATEGORIES.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </div>

              <div className="mt-6">
                <div className="flex items-center justify-between gap-4">
                  <label htmlFor="feedback-content" className="text-sm font-medium text-cloud">反馈内容</label>
                  <span className={`font-mono text-[10px] ${content.length > 1900 ? "text-amber-700" : "text-fog"}`}>
                    {content.length}/2000
                  </span>
                </div>
                <textarea
                  id="feedback-content"
                  required
                  minLength={5}
                  maxLength={2000}
                  rows={10}
                  value={content}
                  onChange={(event) => setContent(event.target.value)}
                  className="input mt-2 resize-y leading-7"
                  placeholder="请尽量描述问题现象、操作步骤，或你希望我们怎样改进"
                />
              </div>

              <div className="mt-6">
                <div className="flex items-center justify-between gap-4">
                  <label htmlFor="feedback-email" className="text-sm font-medium text-cloud">联系邮箱</label>
                  <span className="text-xs text-fog">选填</span>
                </div>
                <input
                  id="feedback-email"
                  type="email"
                  maxLength={320}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="input mt-2 h-12"
                  placeholder="便于我们向你确认问题"
                />
              </div>

              {error && (
                <p className="mt-5 rounded-card border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
              )}

              <div className="mt-7 flex items-center justify-end border-t border-steel pt-6">
                <button
                  type="submit"
                  disabled={busy || content.trim().length < 5 || !category}
                  className="rounded-full bg-cyan px-8 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-45"
                >
                  {busy ? "正在提交…" : "提交反馈"}
                </button>
              </div>
            </form>
          )}
        </section>

        <aside className="paper-card rounded-feature p-6 lg:sticky lg:top-6">
          <p className="eyebrow">如何帮助我们定位</p>
          <h2 className="mt-3 font-serif text-xl text-cloud">一条好反馈最好包含</h2>
          <ol className="mt-6 space-y-5">
            {[
              ["01", "发生了什么", "描述你看到的现象或不符合预期的内容。"],
              ["02", "你做了哪些操作", "提供进入页面后的操作步骤，方便我们复现。"],
              ["03", "你希望怎样改进", "告诉我们更理想的结果或使用方式。"],
            ].map(([number, title, detail]) => (
              <li key={number} className="flex gap-3">
                <span className="font-serif text-lg text-periwinkle">{number}</span>
                <span>
                  <span className="block text-sm text-cloud">{title}</span>
                  <span className="mt-1 block text-xs leading-5 text-fog">{detail}</span>
                </span>
              </li>
            ))}
          </ol>
          <div className="mt-7 rounded-card border border-steel bg-abyss/50 p-4 text-xs leading-6 text-fog">
            请勿在反馈中填写密码、AccessKey、模型 Key 等敏感信息。
          </div>
        </aside>
      </div>
    </div>
  );
}
