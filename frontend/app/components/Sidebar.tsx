"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAuth, getUser, isLoggedIn } from "@/lib/auth";

const NAV = [
  { href: "/", label: "今日日报" },
  { href: "/archive", label: "最近 7 天" },
  { href: "/mine", label: "我的日报" },
  { href: "/landing", label: "产品介绍" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState(false);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    // 登录态只存在于浏览器 localStorage，挂载后同步一次（避免服务端渲染水合不一致）
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoggedIn(isLoggedIn());
    setEmail(getUser()?.email ?? null);
  }, [pathname]);

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  function logout() {
    clearAuth();
    setLoggedIn(false);
    setEmail(null);
    router.push("/");
  }

  return (
    <aside className="flex flex-col border-b border-steel bg-abyss/60 lg:sticky lg:top-0 lg:h-screen lg:w-60 lg:border-b-0 lg:border-r">
      <div className="px-6 py-6">
        <Link href="/" className="font-serif text-xl text-cloud">微蓝日报</Link>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-cyan">Blue Hour Daily</p>
      </div>

      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:gap-0 lg:pb-0">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`whitespace-nowrap rounded-md px-3 py-2 text-sm transition-colors ${
              isActive(item.href) ? "bg-cyan/10 text-cyan" : "text-ash hover:bg-steel/50 hover:text-cloud"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="mt-auto px-3 pb-6 lg:px-6">
        {loggedIn ? (
          <div className="flex flex-col gap-2">
            <span className="truncate font-mono text-xs text-fog">{email}</span>
            <button
              onClick={logout}
              className="rounded-md border border-steel px-3 py-1.5 text-sm text-silver transition-colors hover:border-red-500/50 hover:text-red-400"
            >
              退出登录
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="block rounded-md border border-cyan/40 px-3 py-1.5 text-center text-sm text-cyan transition-colors hover:bg-cyan/10"
          >
            登录 / 注册
          </Link>
        )}
        <p className="mt-4 hidden font-mono text-[10px] uppercase tracking-widest text-fog lg:block">
          在世界醒来之前，看见下一刻。
        </p>
      </div>
    </aside>
  );
}
