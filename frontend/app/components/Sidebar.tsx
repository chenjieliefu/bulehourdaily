"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAuth, getUser, isLoggedIn } from "@/lib/auth";

type NavItem = { href?: string; label: string; soon?: boolean };

// 上组：内容
const TOP_GROUP: NavItem[] = [
  { href: "/mine", label: "订阅日报" },
  { href: "/", label: "公开日报" },
  { href: undefined, label: "邮箱日报", soon: true },
  { href: "/archive", label: "往期归档" },
  { href: undefined, label: "我的收藏", soon: true },
];

// 下组：账户与商业（展示顺序从上到下）
const BOTTOM_GROUP: NavItem[] = [
  { href: undefined, label: "升级会员", soon: true },
  { href: undefined, label: "兑换会员", soon: true },
  { href: undefined, label: "邀请送会员", soon: true },
  { href: undefined, label: "意见反馈", soon: true },
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

  const isActive = (href?: string) =>
    href ? (href === "/" ? pathname === "/" : pathname.startsWith(href)) : false;

  function logout() {
    clearAuth();
    setLoggedIn(false);
    setEmail(null);
    router.push("/");
  }

  const itemCls = (item: NavItem) =>
    item.soon
      ? "cursor-not-allowed whitespace-nowrap rounded-md px-3 py-2 text-sm text-fog/50"
      : `whitespace-nowrap rounded-md px-3 py-2 text-sm transition-colors ${
          isActive(item.href) ? "bg-cyan/10 text-cyan" : "text-ash hover:bg-steel/50 hover:text-cloud"
        }`;

  return (
    <aside className="flex flex-col border-b border-steel bg-abyss/60 lg:sticky lg:top-0 lg:h-screen lg:w-60 lg:border-b-0 lg:border-r">
      {/* Logo */}
      <div className="px-6 py-6">
        <Link href="/" className="block font-serif text-xl text-cloud">微蓝日报</Link>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-cyan">Blue Hour Daily</p>
      </div>

      {/* 上组：内容 */}
      <nav className="flex gap-1 overflow-x-auto px-3 pb-2 lg:flex-col lg:gap-0 lg:pb-0">
        {TOP_GROUP.map((item) => (
          item.href ? (
            <Link key={item.label} href={item.href} className={itemCls(item)}>
              {item.label}
            </Link>
          ) : (
            <span key={item.label} className={itemCls(item)} title="即将上线">{item.label}</span>
          )
        ))}
      </nav>

      {/* 下组：账户与商业 */}
      <nav className="mt-auto flex gap-1 overflow-x-auto border-t border-steel/50 px-3 py-3 lg:flex-col lg:gap-0 lg:border-t-0 lg:py-2">
        {BOTTOM_GROUP.map((item) => (
          item.href ? (
            <Link key={item.label} href={item.href} className={itemCls(item)}>
              {item.label}
            </Link>
          ) : (
            <span key={item.label} className={itemCls(item)} title="即将上线">{item.label}</span>
          )
        ))}
      </nav>

      {/* 底部：头像 + 账号 */}
      <div className="border-t border-steel/50 px-3 py-4 lg:px-4">
        {loggedIn ? (
          <button
            onClick={() => router.push("/mine")}
            className="flex w-full items-center gap-3 rounded-card border border-steel bg-graphite px-3 py-2.5 text-left transition-colors hover:border-cyan/40"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan font-serif text-sm text-obsidian">
              {(email?.[0] ?? "微").toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm text-cloud">{email}</span>
              <span className="block font-mono text-[10px] text-fog">点击进入我的日报</span>
            </span>
          </button>
        ) : (
          <Link
            href="/login"
            className="flex w-full items-center gap-3 rounded-card border border-steel bg-graphite px-3 py-2.5 transition-colors hover:border-cyan/40"
          >
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-steel text-sm text-silver">?</span>
            <span className="text-sm text-ash">登录 / 注册</span>
          </Link>
        )}

        {loggedIn && (
          <button
            onClick={logout}
            className="mt-2 w-full rounded-md px-3 py-1.5 text-left text-xs text-fog transition-colors hover:text-red-400"
          >
            退出登录
          </button>
        )}
      </div>
    </aside>
  );
}
