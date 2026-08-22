import { Suspense } from "react";
import Sidebar from "@/app/components/Sidebar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell min-h-screen lg:flex">
      <Suspense fallback={<div className="hidden border-r border-steel bg-abyss/80 lg:block lg:w-[252px]" />}>
        <Sidebar />
      </Suspense>
      <main className="min-w-0 flex-1 px-5 pb-24 sm:px-8 lg:px-12 xl:px-16">{children}</main>
    </div>
  );
}
