"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiLogin } from "@/lib/api";
import { setAuthSession } from "@/lib/auth";
import { sanitizePassword } from "@/lib/password";
import Brand from "@/app/components/Brand";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await apiLogin(email, password);
      setAuthSession(res.token, res.user);
      router.push(res.user.is_operator ? "/ops" : "/mine");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-obsidian px-6">
      <div className="w-full max-w-sm">
        <Link href="/" className="inline-flex rounded-xl"><Brand /></Link>

        <form onSubmit={onSubmit} className="mt-8 space-y-4">
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
          <Field label="密码">
            <input
              type="password"
              required
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
            {busy ? "登录中…" : "登录"}
          </button>
        </form>

        <p className="mt-6 text-sm text-fog">
          还没有账号？{" "}
          <Link href="/register" className="text-cyan hover:underline">用邀请码注册</Link>
        </p>
        <p className="mt-2 text-sm text-fog">
          <Link href="/" className="hover:text-cloud">← 返回日报</Link>
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
