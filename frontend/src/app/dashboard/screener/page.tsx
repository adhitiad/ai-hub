"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { screenerService } from "@/services/api";
import type { SignalItem } from "@/types";
import {
  Filter,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";

export default function ScreenerPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [results, setResults] = useState<SignalItem[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [signalOnly, setSignalOnly] = useState(false);
  const [bandarAccum, setBandarAccum] = useState(false);
  const [rsiMin, setRsiMin] = useState(0);
  const [rsiMax, setRsiMax] = useState(100);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const runScreener = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await screenerService.run({
        signal_only: signalOnly,
        bandar_accum: bandarAccum,
        rsi_min: rsiMin,
        rsi_max: rsiMax,
      });
      setResults(data.matches || []);
      setCount(data.count || 0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal menjalankan screener";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) runScreener();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const getActionBadge = (action?: string) => {
    const a = (action || "HOLD").toUpperCase();
    if (a === "BUY" || a === "STRONG BUY")
      return (
        <span className="flex items-center gap-1 text-trade-up bg-trade-up/15 px-2.5 py-1 rounded-full text-xs font-bold">
          <TrendingUp className="w-3 h-3" /> {a}
        </span>
      );
    if (a === "SELL" || a === "STRONG SELL")
      return (
        <span className="flex items-center gap-1 text-trade-down bg-trade-down/15 px-2.5 py-1 rounded-full text-xs font-bold">
          <TrendingDown className="w-3 h-3" /> {a}
        </span>
      );
    return (
      <span className="flex items-center gap-1 text-muted-foreground bg-white/10 px-2.5 py-1 rounded-full text-xs font-bold">
        <Minus className="w-3 h-3" /> {a}
      </span>
    );
  };

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
              Stock Screener
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              🔍 Filter aset berdasarkan sinyal AI — <span className="text-chart-5 font-japanese">スクリーナー</span>
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                showFilters ? "bg-primary/20 text-primary" : "glass-panel text-muted-foreground hover:text-foreground"
              }`}
            >
              <SlidersHorizontal className="w-4 h-4" /> Filter
            </button>
            <button
              onClick={runScreener}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/20 text-primary text-sm font-medium hover:bg-primary/30 transition-all cursor-pointer disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Scan
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="glass-panel rounded-xl p-5 mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={signalOnly}
                onChange={(e) => setSignalOnly(e.target.checked)}
                className="rounded accent-primary"
              />
              <span>Signal Only (BUY/SELL)</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={bandarAccum}
                onChange={(e) => setBandarAccum(e.target.checked)}
                className="rounded accent-primary"
              />
              <span>Bandar Akumulasi</span>
            </label>
            <div>
              <label className="text-xs text-muted-foreground">RSI Min</label>
              <input
                type="number"
                value={rsiMin}
                onChange={(e) => setRsiMin(Number(e.target.value))}
                min={0}
                max={100}
                className="w-full mt-1 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">RSI Max</label>
              <input
                type="number"
                value={rsiMax}
                onChange={(e) => setRsiMax(Number(e.target.value))}
                min={0}
                max={100}
                className="w-full mt-1 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
              />
            </div>
          </div>
        )}

        {/* Results Count */}
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-primary" />
          <span className="text-sm text-muted-foreground">
            Ditemukan <span className="text-foreground font-bold">{count}</span> aset
          </span>
        </div>

        {/* Results Table */}
        {error ? (
          <div className="glass-panel rounded-xl p-8 text-center text-trade-down">{error}</div>
        ) : loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="glass-panel rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-muted-foreground">
                  <th className="text-left px-4 py-3 font-medium">Symbol</th>
                  <th className="text-left px-4 py-3 font-medium">Action</th>
                  <th className="text-right px-4 py-3 font-medium">Confidence</th>
                  <th className="text-right px-4 py-3 font-medium">Price</th>
                  <th className="text-right px-4 py-3 font-medium">TP</th>
                  <th className="text-right px-4 py-3 font-medium">SL</th>
                </tr>
              </thead>
              <tbody>
                {results.map((item, i) => (
                  <tr
                    key={`${item.symbol}-${i}`}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                    onClick={() => router.push(`/dashboard/market?symbol=${item.symbol}`)}
                  >
                    <td className="px-4 py-3 font-medium">{item.symbol}</td>
                    <td className="px-4 py-3">{getActionBadge(item.Action)}</td>
                    <td className="px-4 py-3 text-right font-mono">
                      {item.Confidence != null ? `${(item.Confidence as number).toFixed(1)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {item.Price?.toLocaleString() ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-trade-up">
                      {(item as Record<string, unknown>).TP
                        ? Number((item as Record<string, unknown>).TP).toLocaleString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-trade-down">
                      {(item as Record<string, unknown>).SL
                        ? Number((item as Record<string, unknown>).SL).toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))}
                {results.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      Tidak ada aset yang cocok dengan filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
