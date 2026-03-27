"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { backtestService } from "@/services/api";
import type { BacktestResult } from "@/types";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  TestTubeDiagonal,
  Play,
  Loader2,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  Zap,
} from "lucide-react";

export default function BacktestPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // Form
  const [symbol, setSymbol] = useState("BBCA.JK");
  const [period, setPeriod] = useState("2y");
  const [balance, setBalance] = useState("100000000");

  // Result
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    setHasRun(true);
    try {
      const { data } = await backtestService.run(symbol, period, Number(balance));
      setResult(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal menjalankan backtest";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
            Backtest Engine
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            🧪 Simulasi strategi pada data historis — <span className="text-chart-5">バックテスト</span>
          </p>
        </div>

        {/* Input Form */}
        <div className="glass-panel rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">Symbol</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="BBCA.JK"
                className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm font-medium outline-none focus:border-primary/40 transition-colors"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">Period</label>
              <div className="flex gap-1">
                {["6m", "1y", "2y", "5y"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                      period === p
                        ? "bg-primary/20 text-primary border border-primary/30"
                        : "bg-white/5 text-muted-foreground border border-white/10 hover:bg-white/10"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1.5 block">Saldo Awal (IDR)</label>
              <input
                type="number"
                value={balance}
                onChange={(e) => setBalance(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm font-mono outline-none focus:border-primary/40 transition-colors"
              />
            </div>
            <button
              onClick={runBacktest}
              disabled={loading || !symbol}
              className="py-2.5 rounded-lg bg-gradient-to-r from-emerald-600 to-purple-600 text-white font-medium hover:opacity-90 transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Jalankan Backtest
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="px-4 py-3 mb-4 rounded-lg bg-trade-down/10 border border-trade-down/20 text-trade-down text-sm">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="relative">
              <Loader2 className="w-12 h-12 animate-spin text-primary" />
              <Zap className="w-5 h-5 text-chart-4 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className="text-sm text-muted-foreground animate-pulse">
              Menjalankan simulasi pada data historis {period}...
            </p>
          </div>
        )}

        {/* Results */}
        {!loading && result && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                {
                  label: "Total Trades",
                  value: result.total_trades ?? 0,
                  icon: Target,
                  color: "text-chart-3",
                },
                {
                  label: "Win Rate",
                  value: `${(result.win_rate ?? 0).toFixed(1)}%`,
                  icon: BarChart3,
                  color: (result.win_rate ?? 0) >= 50 ? "text-trade-up" : "text-trade-down",
                },
                {
                  label: "Net P&L",
                  value: (result.net_pnl ?? 0).toLocaleString(),
                  icon: (result.net_pnl ?? 0) >= 0 ? TrendingUp : TrendingDown,
                  color: (result.net_pnl ?? 0) >= 0 ? "text-trade-up" : "text-trade-down",
                },
                {
                  label: "Max Drawdown",
                  value: `${(result.max_drawdown ?? 0).toFixed(1)}%`,
                  icon: TrendingDown,
                  color: "text-trade-down",
                },
                {
                  label: "Sharpe Ratio",
                  value: (result.sharpe_ratio ?? 0).toFixed(2),
                  icon: Zap,
                  color: (result.sharpe_ratio ?? 0) >= 1 ? "text-chart-4" : "text-muted-foreground",
                },
              ].map((card) => (
                <div key={card.label} className="glass-panel rounded-xl p-4 text-center">
                  <card.icon className={`w-5 h-5 mx-auto mb-2 ${card.color}`} />
                  <p className={`text-xl font-bold ${card.color}`}>{card.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{card.label}</p>
                </div>
              ))}
            </div>

            {/* Equity Curve */}
            {result.equity_curve && result.equity_curve.length > 0 && (
              <div className="glass-panel rounded-xl p-6" style={{ height: 350 }}>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">📈 Equity Curve — {symbol}</h3>
                <ResponsiveContainer width="100%" height="90%">
                  <AreaChart data={result.equity_curve.map((v, i) => ({ trade: i + 1, equity: v }))}>
                    <defs>
                      <linearGradient id="btEqGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--chart-3)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="var(--chart-3)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="trade"
                      tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }}
                      label={{ value: "Trade #", position: "insideBottom", offset: -5, fontSize: 10, fill: "rgba(255,255,255,0.3)" }}
                    />
                    <YAxis tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(0,0,0,0.8)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(value) => [Number(value).toLocaleString(), "Equity"]}
                    />
                    <Area type="monotone" dataKey="equity" stroke="var(--chart-3)" fill="url(#btEqGrad)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Trades Table */}
            {result.trades && result.trades.length > 0 && (
              <div className="glass-panel rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-white/10">
                  <h3 className="text-sm font-medium text-muted-foreground">Daftar Trade ({result.trades.length})</h3>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-background/80 backdrop-blur-sm">
                      <tr className="border-b border-white/10 text-muted-foreground">
                        <th className="text-left px-4 py-2 font-medium">#</th>
                        <th className="text-left px-4 py-2 font-medium">Action</th>
                        <th className="text-right px-4 py-2 font-medium">Entry</th>
                        <th className="text-right px-4 py-2 font-medium">Exit</th>
                        <th className="text-right px-4 py-2 font-medium">P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map((t, i) => (
                        <tr key={i} className="border-b border-white/5">
                          <td className="px-4 py-2 text-muted-foreground">{i + 1}</td>
                          <td className={`px-4 py-2 font-bold text-xs ${
                            t.action === "BUY" ? "text-trade-up" : "text-trade-down"
                          }`}>{t.action}</td>
                          <td className="px-4 py-2 text-right font-mono">{t.entry_price?.toLocaleString()}</td>
                          <td className="px-4 py-2 text-right font-mono">{t.exit_price?.toLocaleString() ?? "—"}</td>
                          <td className={`px-4 py-2 text-right font-mono font-bold ${
                            (t.pnl ?? 0) >= 0 ? "text-trade-up" : "text-trade-down"
                          }`}>
                            {(t.pnl ?? 0) >= 0 ? "+" : ""}{(t.pnl ?? 0).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !result && hasRun && (
          <div className="glass-panel rounded-xl p-12 text-center text-muted-foreground">
            Tidak ada hasil. Coba simbol atau periode lain.
          </div>
        )}

        {!hasRun && !loading && (
          <div className="glass-panel rounded-xl p-16 text-center">
            <TestTubeDiagonal className="w-16 h-16 mx-auto text-muted-foreground opacity-20 mb-4" />
            <p className="text-muted-foreground">Masukkan parameter dan klik <span className="text-primary font-medium">Jalankan Backtest</span></p>
          </div>
        )}
      </main>
    </div>
  );
}
