"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiRegister } from "@/lib/api";
import { setAuthSession } from "@/lib/auth";
import { sanitizePassword } from "@/lib/password";
import Brand from "@/app/components/Brand";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await apiRegister(email, password, inviteCode);
      setAuthSession(res.token, res.user);
      router.push("/profile");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-obsidian px-6 py-10">
      <div className="w-full max-w-sm">
        <Link href="/" className="inline-flex rounded-xl"><Brand /></Link>

        <h1 className="mt-8 font-serif text-xl text-cloud">邀请制注册</h1>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <Field label="邀请码">
            <input
              required
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              className="input"
              placeholder="例如 WEILAN001"
            />
          </Field>
          <Field label="邮箱">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="you@example.com"
            />
          </Field>
          <Field label="密码（6-128 位，不含空格）">
            <input
              type="password"
              required
              minLength={6}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(sanitizePassword(e.target.value))}
              className="input"
              placeholder="••••••••"
            />
          </Field>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-full bg-cyan py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {busy ? "注册中…" : "注册并填写画像"}
          </button>
        </form>

        <p className="mt-6 text-sm text-fog">
          已有账号？{" "}
          <Link href="/login" className="text-cyan hover:underline">去登录</Link>
        </p>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="font-mono text-xs uppercase tracking-widest text-fog">{label}</span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
