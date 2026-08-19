"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "今日日报" },
  { href: "/archive", label: "最近 7 天" },
  { href: "/landing", label: "产品介绍" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="flex flex-col border-b border-steel bg-abyss/60 lg:sticky lg:top-0 lg:h-screen lg:w-60 lg:border-b-0 lg:border-r">
      <div className="px-6 py-6">
        <Link href="/" className="font-serif text-xl text-cloud">
          微蓝日报
        </Link>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-cyan">
          Blue Hour Daily
        </p>
      </div>

      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:gap-0 lg:pb-0">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`whitespace-nowrap rounded-md px-3 py-2 text-sm transition-colors ${
              isActive(item.href)
                ? "bg-cyan/10 text-cyan"
                : "text-ash hover:bg-steel/50 hover:text-cloud"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="mt-auto hidden px-6 pb-6 lg:block">
        <p className="font-mono text-[10px] uppercase tracking-widest text-fog">
          在世界醒来之前，看见下一刻。
        </p>
      </div>
    </aside>
  );
}
