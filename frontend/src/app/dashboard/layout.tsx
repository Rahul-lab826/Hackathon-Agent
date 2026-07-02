"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Rocket, LayoutDashboard, Plus, Settings,
  LogOut, ChevronRight, User, Bell, MessageSquare, Database, BarChart3
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { api } from "@/lib/api";
import { toast } from "sonner";

const NAV = [
  { href: "/dashboard",           icon: LayoutDashboard, label: "Dashboard"       },
  { href: "/dashboard/chat",      icon: MessageSquare,   label: "AI Chat"         },
  { href: "/dashboard/memory",    icon: Database,        label: "Memory Explorer" },
  { href: "/dashboard/analytics", icon: BarChart3,       label: "Analytics Hub"   },
  { href: "/dashboard/new-event", icon: Plus,            label: "New Event"      },
  { href: "/dashboard/settings",  icon: Settings,        label: "Settings"       },
];

function Sidebar() {
  const pathname  = usePathname();
  const router    = useRouter();
  const { user, clearAuth, refreshToken } = useAuthStore();

  const handleLogout = async () => {
    try {
      if (refreshToken) await api.post("/auth/logout", { refresh_token: refreshToken });
    } catch { /* silent */ } finally {
      clearAuth();
      router.push("/login");
      toast.success("Logged out successfully.");
    }
  };

  return (
    <aside className="flex flex-col w-64 min-h-screen bg-dark-400 border-r border-white/5 py-6 px-4">
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-3 px-2 mb-8 group">
        <div className="w-9 h-9 rounded-xl bg-gradient-brand flex items-center justify-center shadow-glow-sm group-hover:scale-105 transition-transform">
          <Rocket className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="font-display font-bold text-white text-sm leading-none">HackLaunch</p>
          <p className="text-xs text-brand-400 font-medium">AI Platform</p>
        </div>
      </Link>

      {/* Nav */}
      <nav className="flex-1 space-y-1">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                active
                  ? "bg-brand-600/20 text-brand-300 border border-brand-500/25"
                  : "text-surface-500 hover:text-surface-200 hover:bg-white/4"
              )}>
              <Icon className={cn("w-4 h-4", active ? "text-brand-400" : "text-surface-600")} />
              {label}
              {active && <ChevronRight className="w-3 h-3 ml-auto text-brand-500" />}
            </Link>
          );
        })}
      </nav>

      {/* User card */}
      <div className="glass-card rounded-xl p-3 mt-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-brand flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            {user?.full_name?.charAt(0)?.toUpperCase() ?? <User className="w-4 h-4" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">{user?.full_name ?? "User"}</p>
            <p className="text-surface-600 text-xs truncate">{user?.email}</p>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-surface-600 capitalize bg-white/5 px-2 py-0.5 rounded-full border border-white/6">
            {user?.plan ?? "free"}
          </span>
          <button onClick={handleLogout}
            className="flex items-center gap-1.5 text-xs text-surface-600 hover:text-red-400 transition-colors">
            <LogOut className="w-3 h-3" />
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-dark-500">
      {/* Fixed ambient */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 right-1/3 w-[400px] h-[400px] bg-brand-600/6 rounded-full blur-[100px]" />
        <div className="absolute bottom-0 left-1/3 w-[300px] h-[300px] bg-accent-600/6 rounded-full blur-[80px]" />
      </div>

      <Sidebar />

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        {/* Topbar */}
        <header className="flex items-center justify-between px-8 py-4 border-b border-white/5 bg-dark-400/50 backdrop-blur-sm">
          <div />
          <div className="flex items-center gap-3">
            <button className="w-9 h-9 glass rounded-xl flex items-center justify-center text-surface-500 hover:text-white transition-colors">
              <Bell className="w-4 h-4" />
            </button>
            <Link href="/dashboard/settings"
              className="w-9 h-9 glass rounded-xl flex items-center justify-center text-surface-500 hover:text-white transition-colors">
              <Settings className="w-4 h-4" />
            </Link>
          </div>
        </header>

        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
