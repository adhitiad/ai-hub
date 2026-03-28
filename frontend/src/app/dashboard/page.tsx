"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { DashboardOverview } from "@/components/dashboard-overview";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="space-y-6">
      {/* Top bar (Page Specific) */}
      <header className="flex items-center justify-between py-4 border-b border-white/5">
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Dashboard</h2>
          <p className="text-xs text-muted-foreground">
            リアルタイムモニター — Global AI Trading Overview
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-medium text-emerald-400">ENGINE LIVE</span>
          </div>
        </div>
      </header>

      {/* Content */}
      <DashboardOverview />
    </div>
  );
}
