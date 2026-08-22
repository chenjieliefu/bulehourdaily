"use client";

import { useEffect, useRef, useState } from "react";
import { apiRegister } from "@/lib/api";
import { setAuthSession, type AuthUser } from "@/lib/auth";
import { sanitizePassword } from "@/lib/password";

type RegisterDialogProps = {
  open: boolean;
  onClose: () => void;
  onSuccess: (user: AuthUser) => void;
  onLogin: () => void;
};

export default function RegisterDialog({ open, onClose, onSuccess, onLogin }: RegisterDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inviteCodeRef = useRef<HTMLInputElement>(null);
  const [inviteCode, setInviteCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
      setError(null);
      requestAnimationFrame(() => inviteCodeRef.current?.focus());
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await apiRegister(email, password, inviteCode);
      setAuthSession(response.token, response.user);
      onSuccess(response.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setBusy(false);
    }
  }

  function requestClose() {
    if (!busy) onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="register-dialog-title"
      aria-describedby="register-dialog-description"
      onCancel={(event) => {
        event.preventDefault();
        requestClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) requestClose();
      }}
      className="m-auto max-h-[90vh] w-[min(94vw,680px)] overflow-y-auto rounded-[28px] border border-steel bg-white p-0 text-cloud shadow-2xl backdrop:bg-slate-950/35 backdrop:backdrop-blur-sm"
    >
      <div className="relative grid md:grid-cols-[0.85fr_1.4fr]">
        <button
          type="button"
          onClick={requestClose}
          disabled={busy}
          aria-label="关闭注册窗口"
          className="absolute right-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-full text-xl text-fog transition-colors hover:bg-abyss hover:text-cloud disabled:opacity-40"
        >
          ×
        </button>

        <section className="bg-abyss px-6 py-8 md:px-8 md:py-10">
          <p className="eyebrow">Invitation Only</p>
          <h2 id="register-dialog-title" className="mt-3 pr-10 font-serif text-3xl text-cloud md:pr-0">
            创建微蓝账号
          </h2>
          <p id="register-dialog-description" className="mt-3 text-sm leading-6 text-fog">
            使用邀请码完成注册，登录后即可查看全部往期日报。
          </p>
        </section>

        <section className="px-6 py-8 md:px-8 md:py-10">
          <form onSubmit={onSubmit} className="space-y-4">
            <label className="block">
              <span className="font-mono text-xs uppercase tracking-widest text-fog">邀请码</span>
              <input
                ref={inviteCodeRef}
                required
                value={inviteCode}
                onChange={(event) => setInviteCode(event.target.value)}
                className="input mt-1.5"
                placeholder="例如 WEILAN001"
              />
            </label>
            <label className="block">
              <span className="font-mono text-xs uppercase tracking-widest text-fog">邮箱</span>
              <input
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="input mt-1.5"
                placeholder="you@example.com"
              />
            </label>
            <label className="block">
              <span className="font-mono text-xs uppercase tracking-widest text-fog">密码（6-128 位，不含空格）</span>
              <input
                type="password"
                required
                minLength={6}
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(sanitizePassword(event.target.value))}
                className="input mt-1.5"
                placeholder="••••••••"
              />
            </label>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-full bg-cyan py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {busy ? "注册中…" : "完成注册"}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-fog">
            已有账号？{" "}
            <button type="button" onClick={onLogin} className="text-cyan hover:underline">
              返回登录
            </button>
          </p>
        </section>
      </div>
    </dialog>
  );
}
