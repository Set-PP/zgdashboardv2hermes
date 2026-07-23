"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, HardHat, FileText, Images, FolderOpen, Settings,
  Bell, Search, ArrowLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "My Sites", href: "/dashboard/sites", icon: HardHat },
  { label: "Daily Reports", href: "/dashboard/reports", icon: FileText },
  { label: "Gallery", href: "/dashboard/gallery", icon: Images },
  { label: "Documents", href: "/dashboard/docs", icon: FolderOpen },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-ink">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-line bg-ink-2 lg:flex">
        <div className="flex items-center justify-between px-6 py-6">
          <Link href="/" className="font-display text-xl font-semibold tracking-tight">
            ZAW&nbsp;G
            <span className="ml-2 text-[9px] font-normal uppercase tracking-[0.3em] text-bronze">Portal</span>
          </Link>
        </div>

        <nav className="mt-4 flex-1 space-y-1 px-3">
          {NAV.map((n) => {
            const active = pathname === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-4 py-3 text-[13px] transition-all duration-300",
                  active
                    ? "bg-bronze/10 text-bronze"
                    : "text-mute hover:bg-ink-3 hover:text-bone"
                )}
              >
                <n.icon className={cn("h-4 w-4", active && "text-bronze")} />
                {n.label}
                {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-bronze" />}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-line p-4">
          <div className="flex items-center gap-3 rounded-xl bg-ink-3 p-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-bronze font-display text-sm font-semibold text-ink">
              AK
            </span>
            <div className="min-w-0">
              <p className="truncate text-[13px] text-bone">U Aung Khant</p>
              <p className="truncate text-[10px] uppercase tracking-widest text-mute">54B Residence</p>
            </div>
          </div>
          <Link
            href="/"
            className="mt-3 flex items-center gap-2 px-2 text-[11px] uppercase tracking-[0.2em] text-mute transition-colors hover:text-bronze"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to site
          </Link>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 lg:pl-64">
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex items-center gap-4 border-b border-line bg-ink/80 px-6 py-4 backdrop-blur-xl lg:px-10">
          <div className="flex flex-1 items-center gap-3 rounded-xl border border-line bg-ink-2 px-4 py-2.5 text-sm text-mute">
            <Search className="h-4 w-4" />
            <input
              placeholder="Search reports, photos, documents…"
              className="w-full bg-transparent text-bone outline-none placeholder:text-mute/60"
            />
          </div>
          <button className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-ink-2 text-mute transition-colors hover:text-bronze">
            <Bell className="h-4 w-4" />
            <span className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-bronze" />
          </button>
        </header>

        <main className="px-6 py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
