"use client";

import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import {
  LayoutDashboard,
  LineChart,
  Settings,
  LogOut,
  Zap,
  Shield,
  Search,
  Bell,
  Filter,
  BookOpen,
  TestTubeDiagonal,
  Wallet,
  MessageCircle,
  CreditCard,
  Users,
  Crown,
  FileText,
  Play,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: string[]; // Jika undefined = semua role
  badge?: string;
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Market", href: "/dashboard/market", icon: LineChart },
  { label: "Screener", href: "/dashboard/screener", icon: Filter },
  { label: "Alerts", href: "/dashboard/alerts", icon: Bell },
  { label: "Analysis", href: "/dashboard/analysis", icon: FileText },
  { label: "Simulation", href: "/dashboard/simulation", icon: Play },
  { label: "Journal", href: "/dashboard/journal", icon: BookOpen },
  { label: "Backtest", href: "/dashboard/backtest", icon: TestTubeDiagonal },
  { label: "Portfolio", href: "/dashboard/portfolio", icon: Wallet },
  { label: "AI Chat", href: "/dashboard/chat", icon: MessageCircle },
  { label: "Pricing", href: "/dashboard/pricing", icon: CreditCard },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
  {
    label: "Admin",
    href: "/dashboard/admin",
    icon: Users,
    roles: ["admin", "owner"],
    badge: "Staff",
  },
  {
    label: "Owner",
    href: "/dashboard/owner",
    icon: Crown,
    roles: ["owner"],
    badge: "Super",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const userRole = user?.role ?? "free";

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const visibleItems = navItems.filter(
    (item) => !item.roles || item.roles.includes(userRole)
  );

  return (
    <aside className="fixed top-0 left-0 z-40 h-screen w-64 flex flex-col border-r border-white/10 glass-panel">
      {/* Logo Area */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/10">
        <div className="relative">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-purple-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 animate-pulse border-2 border-background" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
            AI Trading Hub
          </h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest">
            Neural Engine v2
          </p>
        </div>
      </div>

      {/* Search Button */}
      <div className="px-3 pt-3">
        <button
          onClick={() => router.push("/dashboard/market")}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground bg-white/5 hover:bg-white/10 border border-white/5 transition-all cursor-pointer"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="text-xs">Cari aset...</span>
          <kbd className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-white/10 font-mono">
            /
          </kbd>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {visibleItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer",
                isActive
                  ? "bg-primary/20 text-primary shadow-sm shadow-primary/10 border border-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              <item.icon
                className={cn("w-4 h-4 shrink-0", isActive && "text-primary")}
              />
              <span className="truncate">{item.label}</span>
              {item.badge && (
                <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full bg-chart-5/20 text-chart-5 font-bold uppercase tracking-wider">
                  {item.badge}
                </span>
              )}
              {isActive && !item.badge && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              )}
            </button>
          );
        })}
      </nav>

      {/* User area */}
      <div className="px-3 py-3 border-t border-white/10 space-y-1.5">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate">
              {user?.email ?? "User"}
            </p>
            <p className="text-[10px] text-muted-foreground uppercase">
              {userRole}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-trade-down hover:bg-trade-down/10 transition-all duration-200 cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
