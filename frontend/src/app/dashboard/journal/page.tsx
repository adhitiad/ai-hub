"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { journalService } from "@/services/api";
import type { TradeHistory, TradingStats } from "@/types";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  BookOpen,
  TrendingUp,
  TrendingDown,
  Target,
  Award,
  BarChart3,
  Loader2,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Flame,
} from "lucide-react";

export default function JournalPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"history" | "stats">("stats");
  const [history, setHistory] = useState<TradeHistory[]>([]);
  const [stats, setStats] = useState<TradingStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await journalService.getHistory(100);
      setHistory(data);
    } catch {
      setError("Gagal memuat riwayat trading");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await journalService.getStats();
      setStats(data);
    } catch {
      setError("Gagal memuat statistik");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (activeTab === "stats") fetchStats();
    else fetchHistory();
  }, [activeTab, isAuthenticated, fetchStats, fetchHistory]);

  const COLORS_PIE = ["var(--trade-up)", "var(--trade-down)"];

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
              Trading Journal
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              📓 Catatan & analisis performa — <span className="text-chart-5">ジャーナル</span>
            </p>
          </div>
          <div className="flex gap-1 p-1 glass-panel rounded-xl">
            {[
              { key: "stats" as const, label: "Statistik", icon: BarChart3 },
              { key: "history" as const, label: "Riwayat", icon: Calendar },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  activeTab === tab.key
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="px-4 py-3 mb-4 rounded-lg bg-trade-down/10 border border-trade-down/20 text-trade-down text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : activeTab === "stats" && stats ? (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                {
                  label: "Total Trades",
                  value: stats.total_trades,
                  icon: Target,
                  color: "text-chart-3",
                  bg: "bg-chart-3/10",
                },
                {
                  label: "Win Rate",
                  value: `${stats.win_rate?.toFixed(1)}%`,
                  icon: Award,
                  color: stats.win_rate >= 50 ? "text-trade-up" : "text-trade-down",
                  bg: stats.win_rate >= 50 ? "bg-trade-up/10" : "bg-trade-down/10",
                },
                {
                  label: "Total P&L",
                  value: `${stats.total_pnl >= 0 ? "+" : ""}${stats.total_pnl?.toLocaleString()}`,
                  icon: stats.total_pnl >= 0 ? TrendingUp : TrendingDown,
                  color: stats.total_pnl >= 0 ? "text-trade-up" : "text-trade-down",
                  bg: stats.total_pnl >= 0 ? "bg-trade-up/10" : "bg-trade-down/10",
                },
                {
                  label: "Profit Factor",
                  value: stats.profit_factor?.toFixed(2),
                  icon: Flame,
                  color: stats.profit_factor >= 1 ? "text-chart-4" : "text-trade-down",
                  bg: "bg-chart-4/10",
                },
              ].map((card) => (
                <div key={card.label} className="glass-panel rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center`}>
                      <card.icon className={`w-4 h-4 ${card.color}`} />
                    </div>
                    <span className="text-xs text-muted-foreground">{card.label}</span>
                  </div>
                  <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                </div>
              ))}
            </div>

            {/* Second Row Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Avg Win", value: `+${stats.avg_win?.toLocaleString()}`, color: "text-trade-up" },
                { label: "Avg Loss", value: stats.avg_loss?.toLocaleString(), color: "text-trade-down" },
                { label: "Best Trade", value: `+${stats.best_trade?.toLocaleString()}`, color: "text-trade-up" },
                { label: "Max Drawdown", value: `${stats.max_drawdown?.toFixed(1)}%`, color: "text-trade-down" },
              ].map((item) => (
                <div key={item.label} className="glass-panel rounded-xl p-4 text-center">
                  <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                  <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
                </div>
              ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Equity Curve */}
              <div className="md:col-span-2 glass-panel rounded-xl p-5" style={{ height: 320 }}>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">📈 Equity Curve</h3>
                <ResponsiveContainer width="100%" height="90%">
                  <AreaChart
                    data={(stats.equity_curve || []).map((v, i) => ({ idx: i + 1, equity: v }))}
                  >
                    <defs>
                      <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--trade-up)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="var(--trade-up)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="idx" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} />
                    <YAxis tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(0,0,0,0.8)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Area type="monotone" dataKey="equity" stroke="var(--trade-up)" fill="url(#eqGrad)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Win/Loss Pie */}
              <div className="glass-panel rounded-xl p-5" style={{ height: 320 }}>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">🎯 Win vs Loss</h3>
                <ResponsiveContainer width="100%" height="80%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: "Win", value: stats.win_rate || 0 },
                        { name: "Loss", value: 100 - (stats.win_rate || 0) },
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {COLORS_PIE.map((c, i) => (
                        <Cell key={i} fill={c} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "rgba(0,0,0,0.8)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 text-xs">
                  <span className="flex items-center gap-1 text-trade-up">● Win {stats.win_rate?.toFixed(1)}%</span>
                  <span className="flex items-center gap-1 text-trade-down">● Loss {(100 - (stats.win_rate || 0)).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === "history" ? (
          /* History Table */
          <div className="glass-panel rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-muted-foreground">
                  <th className="text-left px-4 py-3 font-medium">Symbol</th>
                  <th className="text-left px-4 py-3 font-medium">Action</th>
                  <th className="text-right px-4 py-3 font-medium">Entry</th>
                  <th className="text-right px-4 py-3 font-medium">Exit</th>
                  <th className="text-right px-4 py-3 font-medium">Qty</th>
                  <th className="text-right px-4 py-3 font-medium">P&L</th>
                  <th className="text-right px-4 py-3 font-medium">%</th>
                  <th className="text-left px-4 py-3 font-medium">Status</th>
                  <th className="text-left px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((t, i) => {
                  const pnl = t.pnl ?? 0;
                  return (
                    <tr
                      key={t.id || t._id || i}
                      className="border-b border-white/5 hover:bg-white/5 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">{t.symbol}</td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1 text-xs font-bold ${
                          t.action === "BUY" ? "text-trade-up" : "text-trade-down"
                        }`}>
                          {t.action === "BUY" ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                          {t.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono">{t.entry_price?.toLocaleString()}</td>
                      <td className="px-4 py-3 text-right font-mono">{t.exit_price?.toLocaleString() ?? "—"}</td>
                      <td className="px-4 py-3 text-right font-mono">{t.quantity}</td>
                      <td className={`px-4 py-3 text-right font-mono font-bold ${pnl >= 0 ? "text-trade-up" : "text-trade-down"}`}>
                        {pnl >= 0 ? "+" : ""}{pnl.toLocaleString()}
                      </td>
                      <td className={`px-4 py-3 text-right font-mono text-xs ${pnl >= 0 ? "text-trade-up" : "text-trade-down"}`}>
                        {t.pnl_percent != null ? `${t.pnl_percent.toFixed(1)}%` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          t.status === "CLOSED" ? "bg-white/10 text-muted-foreground"
                          : t.status === "OPEN" ? "bg-trade-up/15 text-trade-up"
                          : "bg-chart-4/15 text-chart-4"
                        }`}>
                          {t.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">
                        {t.entry_date ? new Date(t.entry_date).toLocaleDateString("id-ID") : "—"}
                      </td>
                    </tr>
                  );
                })}
                {history.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">
                      Belum ada riwayat trading.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center justify-center py-20">
            <BookOpen className="w-12 h-12 text-muted-foreground opacity-30" />
          </div>
        )}
      </main>
    </div>
  );
}
