"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getProfile, saveProfile, type Profile } from "@/lib/api";

const FIELDS: { key: keyof Omit<Profile, "updated_at">; label: string; hint: string; textarea?: boolean }[] = [
  { key: "positioning", label: "账号定位", hint: "你的账号主要在做什么内容" },
  { key: "audience", label: "目标观众", hint: "你希望谁看你的视频" },
  { key: "persona", label: "人设", hint: "你在观众眼里是什么形象" },
  { key: "style", label: "表达风格", hint: "你习惯怎么说话（口语、专业…）" },
  { key: "video_length", label: "常见视频长度", hint: "例如 60 秒" },
  { key: "forbidden", label: "内容禁区", hint: "你不想碰的话题" },
];

export default function ProfilePage() {
  const router = useRouter();
  const [form, setForm] = useState<Record<string, string>>({
    positioning: "",
    audience: "",
    persona: "",
    style: "",
    video_length: "",
    forbidden: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await getProfile();
        if (p) {
          setForm({
            positioning: p.positioning,
            audience: p.audience,
            persona: p.persona,
            style: p.style,
            video_length: p.video_length,
            forbidden: p.forbidden,
          });
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    setSaving(true);
    try {
      await saveProfile(form as Profile);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-[640px]">
      <div className="border-b border-steel pb-8 pt-10">
        <p className="font-mono text-xs uppercase tracking-widest text-fog">Creator Profile</p>
        <h1 className="mt-3 font-serif text-2xl text-cloud">创作者画像</h1>
        <p className="mt-2 text-sm text-fog">画像只影响之后生成的日报，已生成的不会变。</p>
      </div>

      {loading && <p className="mt-8 text-fog">加载中…</p>}

      {!loading && (
        <form onSubmit={onSubmit} className="mt-8 space-y-5">
          {FIELDS.map((f) => (
            <label key={f.key} className="block">
              <span className="font-mono text-xs uppercase tracking-widest text-cyan">{f.label}</span>
              <textarea
                required
                rows={f.key === "forbidden" || f.key === "positioning" ? 2 : 2}
                value={form[f.key]}
                onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                className="input mt-1.5 resize-none"
                placeholder={f.hint}
              />
            </label>
          ))}

          {error && <p className="text-sm text-red-400">{error}</p>}
          {saved && (
            <p className="rounded-card border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
              已保存 ✓ 新的画像将在你下次生成个性化日报时生效。
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-full bg-cyan px-8 py-2.5 text-sm font-medium text-obsidian transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "保存中…" : "保存画像"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/mine")}
              className="rounded-full border border-steel px-8 py-2.5 text-sm text-silver transition-colors hover:border-cyan hover:text-cyan"
            >
              去我的日报
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
