"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { AUTH_CHANGE_EVENT, getUser, type AuthUser } from "@/lib/auth";
import LoginDialog from "@/app/components/LoginDialog";
import RegisterDialog from "@/app/components/RegisterDialog";

type AuthMode = "login" | "register" | null;

export default function RequireUser({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null | undefined>(undefined);
  const [mode, setMode] = useState<AuthMode>("login");

  useEffect(() => {
    const sync = () => setUser(getUser("user"));
    sync();
    window.addEventListener(AUTH_CHANGE_EVENT, sync);
    return () => window.removeEventListener(AUTH_CHANGE_EVENT, sync);
  }, []);

  if (user === undefined) {
    return <p className="mx-auto mt-16 max-w-xl text-center text-sm text-fog">正在确认登录状态…</p>;
  }

  if (user) return children;

  function finishAuth(nextUser: AuthUser) {
    if (nextUser.is_operator) {
      router.replace("/ops");
      return;
    }
    setUser(nextUser);
  }

  function closeGate() {
    setMode(null);
    router.replace("/");
  }

  return (
    <>
      <div className="mx-auto mt-16 max-w-xl rounded-feature border border-steel bg-white p-8 text-center shadow-sm">
        <p className="eyebrow">Members Only</p>
        <h1 className="mt-3 font-serif text-2xl text-cloud">登录后查看你的个性化日报</h1>
        <p className="mt-3 text-sm leading-6 text-fog">这里的画像和日报只对你本人可见。</p>
      </div>
      <LoginDialog
        open={mode === "login"}
        onClose={closeGate}
        onSuccess={finishAuth}
        onRegister={() => setMode("register")}
      />
      <RegisterDialog
        open={mode === "register"}
        onClose={closeGate}
        onSuccess={finishAuth}
        onLogin={() => setMode("login")}
      />
    </>
  );
}
