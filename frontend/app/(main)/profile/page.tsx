"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getProfile, saveProfile, type Profile } from "@/lib/api";

type FieldDef = {
  key: keyof Omit<Profile, "updated_at">;
  label: string;
  placeholder: string;
  examples: string[];
};

const FIELDS: FieldDef[] = [
  {
    key: "positioning",
    label: "你的账号主要在做什么内容？",
    placeholder: "一句话说清你的账号定位",
    examples: ["AI 工具测评", "AI 新闻解读", "AI 绘画教程", "AI 变现干货"],
  },
  {
    key: "audience",
    label: "你最想吸引谁看你的视频？",
    placeholder: "描述你的目标观众",
    examples: ["想学 AI 的新手", "AI 从业者", "做副业的普通人", "学生党"],
  },
  {
    key: "persona",
    label: "你在观众眼里是什么形象（人设）？",
    placeholder: "描述你希望塑造的人设",
    examples: ["技术大佬", "邻家老师", "测评达人", "幽默吐槽"],
  },
  {
    key: "style",
    label: "你习惯用什么风格表达？",
    placeholder: "描述你的表达风格",
    examples: ["口语化、爱打比方", "专业严谨", "轻松幽默", "犀利点评"],
  },
  {
    key: "video_length",
    label: "你一般拍多长的视频？",
    placeholder: "填写你的常见视频长度",
    examples: ["30 秒", "60 秒", "1-3 分钟", "3 分钟以上"],
  },
  {
    key: "forbidden",
    label: "你不想碰哪些内容（内容禁区）？",
    placeholder: "填写不想涉及的话题，没有就写「无」",
    examples: ["不碰政治", "不碰医疗", "不碰投资建议", "没有特别禁区"],
  },
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
        <p className="mt-2 text-sm text-fog">
          不知道怎么填？点下面的推荐选项即可，也可以自己写。画像只影响之后生成的日报。
        </p>
      </div>

      {loading && <p className="mt-8 text-fog">加载中…</p>}

      {!loading && (
        <form onSubmit={onSubmit} className="mt-8 space-y-7">
          {FIELDS.map((f) => (
            <div key={f.key}>
              <label className="font-mono text-xs uppercase tracking-widest text-cyan">{f.label}</label>
              <textarea
                required
                rows={2}
                value={form[f.key]}
                onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                className="input mt-2 resize-none"
                placeholder={f.placeholder}
              />
              <div className="mt-2 flex flex-wrap gap-2">
                {f.examples.map((ex) => {
                  const active = form[f.key] === ex;
                  return (
                    <button
                      key={ex}
                      type="button"
                      onClick={() => setForm({ ...form, [f.key]: ex })}
                      className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                        active
                          ? "border-cyan bg-cyan/10 text-cyan"
                          : "border-steel text-silver hover:border-cyan hover:text-cyan"
                      }`}
                    >
                      {ex}
                    </button>
                  );
                })}
              </div>
            </div>
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
