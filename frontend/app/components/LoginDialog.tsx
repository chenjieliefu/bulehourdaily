"use client";

import { useEffect, useRef, useState } from "react";
import { apiLogin } from "@/lib/api";
import { setAuthSession, type AuthUser } from "@/lib/auth";
import { sanitizePassword } from "@/lib/password";

type LoginDialogProps = {
  open: boolean;
  onClose: () => void;
  onSuccess: (user: AuthUser) => void;
  onRegister: () => void;
};

export default function LoginDialog({ open, onClose, onSuccess, onRegister }: LoginDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function resetForm() {
    setEmail("");
    setPassword("");
    setError(null);
  }

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
      setError(null);
      requestAnimationFrame(() => emailRef.current?.focus());
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await apiLogin(email, password);
      setAuthSession(response.token, response.user);
      resetForm();
      onSuccess(response.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setBusy(false);
    }
  }

  function requestClose() {
    if (busy) return;
    resetForm();
    onClose();
  }

  function requestRegister() {
    resetForm();
    onRegister();
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="login-dialog-title"
      aria-describedby="login-dialog-description"
      onCancel={(event) => {
        event.preventDefault();
        requestClose();
      }}
      className="m-auto w-[min(92vw,420px)] rounded-[24px] border border-steel bg-white p-0 text-cloud shadow-2xl backdrop:bg-slate-950/35 backdrop:backdrop-blur-sm"
    >
      <div className="relative px-6 py-7 sm:px-8 sm:py-8">
        <button
          type="button"
          onClick={requestClose}
          disabled={busy}
          aria-label="关闭登录窗口"
          className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-full text-xl text-fog transition-colors hover:bg-abyss hover:text-cloud disabled:opacity-40"
        >
          ×
        </button>

        <h2 id="login-dialog-title" className="pr-10 font-serif text-3xl text-cloud">
          登录
        </h2>
        <p id="login-dialog-description" className="mt-3 text-sm leading-6 text-fog">
          请输入您的邮箱和密码进行登录
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <label className="block">
            <span className="font-mono text-xs uppercase tracking-widest text-fog">邮箱</span>
            <input
              ref={emailRef}
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="input mt-1.5"
              placeholder="you@example.com"
            />
          </label>
          <label className="block">
            <span className="font-mono text-xs uppercase tracking-widest text-fog">密码</span>
            <input
              type="password"
              required
              maxLength={128}
              autoComplete="current-password"
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
            {busy ? "登录中…" : "登录"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-fog">
          还没有账号？{" "}
          <button type="button" onClick={requestRegister} className="text-cyan hover:underline">
            立即注册
          </button>
        </p>
      </div>
    </dialog>
  );
}
