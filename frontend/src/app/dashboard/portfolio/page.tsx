"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { portfolioService, dashboardService } from "@/services/api";
import type { OpenTrade } from "@/types";
import {
  Wallet,
  ArrowUpCircle,
  ArrowDownCircle,
  Loader2,
  Send,
  TrendingUp,
  TrendingDown,
  RefreshCw,
} from "lucide-react";

export default function PortfolioPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  // Open trades
  const [trades, setTrades] = useState<OpenTrade[]>([]);
  const [loading, setLoading] = useState(false);

  // Order form
  const [orderSymbol, setOrderSymbol] = useState("");
  const [orderAction, setOrderAction] = useState<"BUY" | "SELL">("BUY");
  const [orderQty, setOrderQty] = useState("");
  const [orderPrice, setOrderPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [orderResult, setOrderResult] = useState<string | null>(null);
  const [orderError, setOrderError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const fetchTrades = async () => {
    setLoading(true);
    try {
      const { data } = await dashboardService.getOverview();
      setTrades(data.open_trades || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) fetchTrades();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const executeOrder = async () => {
    if (!orderSymbol || !orderQty || !orderPrice) return;
    setSubmitting(true);
    setOrderResult(null);
    setOrderError(null);
    try {
      await portfolioService.executeVirtual(
        orderSymbol.toUpperCase(),
        orderAction,
        Number(orderQty),
        Number(orderPrice)
      );
      setOrderResult(`✅ ${orderAction} ${orderQty} lot ${orderSymbol.toUpperCase()} @ ${Number(orderPrice).toLocaleString()}`);
      setOrderSymbol("");
      setOrderQty("");
      setOrderPrice("");
      fetchTrades();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal eksekusi order";
      setOrderError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const totalPnl = trades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
              Virtual Portfolio
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              💼 Trading simulator — <span className="text-chart-5">ポートフォリオ</span>
            </p>
          </div>
          <button
            onClick={fetchTrades}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg glass-panel text-sm text-muted-foreground hover:text-foreground transition-all cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Order Form */}
          <div className="lg:col-span-1 space-y-4">
            <div className="glass-panel rounded-xl p-6">
              <h2 className="text-sm font-medium text-muted-foreground mb-4">📝 New Order</h2>

              {/* Buy/Sell Toggle */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setOrderAction("BUY")}
                  className={`flex-1 py-3 rounded-lg font-bold text-sm transition-all cursor-pointer flex items-center justify-center gap-2 ${
                    orderAction === "BUY"
                      ? "bg-trade-up/20 text-trade-up border border-trade-up/30"
                      : "bg-white/5 text-muted-foreground border border-white/10"
                  }`}
                >
                  <ArrowUpCircle className="w-4 h-4" /> BUY
                </button>
                <button
                  onClick={() => setOrderAction("SELL")}
                  className={`flex-1 py-3 rounded-lg font-bold text-sm transition-all cursor-pointer flex items-center justify-center gap-2 ${
                    orderAction === "SELL"
                      ? "bg-trade-down/20 text-trade-down border border-trade-down/30"
                      : "bg-white/5 text-muted-foreground border border-white/10"
                  }`}
                >
                  <ArrowDownCircle className="w-4 h-4" /> SELL
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Symbol</label>
                  <input
                    type="text"
                    value={orderSymbol}
                    onChange={(e) => setOrderSymbol(e.target.value)}
                    placeholder="BBCA.JK"
                    className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block">Qty (lot)</label>
                    <input
                      type="number"
                      value={orderQty}
                      onChange={(e) => setOrderQty(e.target.value)}
                      placeholder="1"
                      className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm font-mono outline-none focus:border-primary/40"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block">Harga</label>
                    <input
                      type="number"
                      value={orderPrice}
                      onChange={(e) => setOrderPrice(e.target.value)}
                      placeholder="9000"
                      className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm font-mono outline-none focus:border-primary/40"
                    />
                  </div>
                </div>
              </div>

              <button
                onClick={executeOrder}
                disabled={submitting || !orderSymbol || !orderQty || !orderPrice}
                className={`w-full mt-4 py-3 rounded-lg font-bold text-sm transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2 ${
                  orderAction === "BUY"
                    ? "bg-trade-up/20 text-trade-up hover:bg-trade-up/30"
                    : "bg-trade-down/20 text-trade-down hover:bg-trade-down/30"
                }`}
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Execute {orderAction}
              </button>

              {orderResult && (
                <div className="mt-3 px-3 py-2 rounded-lg bg-trade-up/10 text-trade-up text-xs">{orderResult}</div>
              )}
              {orderError && (
                <div className="mt-3 px-3 py-2 rounded-lg bg-trade-down/10 text-trade-down text-xs">{orderError}</div>
              )}
            </div>

            {/* Portfolio Summary */}
            <div className="glass-panel rounded-xl p-6">
              <h2 className="text-sm font-medium text-muted-foreground mb-3">Summary</h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Open Positions</span>
                  <span className="text-sm font-bold">{trades.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">Unrealized P&L</span>
                  <span className={`text-sm font-bold ${totalPnl >= 0 ? "text-trade-up" : "text-trade-down"}`}>
                    {totalPnl >= 0 ? "+" : ""}{totalPnl.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Open Trades Table */}
          <div className="lg:col-span-2">
            <div className="glass-panel rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
                <Wallet className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-medium">Open Positions</h3>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : trades.length === 0 ? (
                <div className="p-12 text-center">
                  <Wallet className="w-10 h-10 mx-auto text-muted-foreground opacity-30 mb-3" />
                  <p className="text-muted-foreground text-sm">Belum ada posisi terbuka.</p>
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-muted-foreground">
                      <th className="text-left px-4 py-3 font-medium">Symbol</th>
                      <th className="text-left px-4 py-3 font-medium">Side</th>
                      <th className="text-right px-4 py-3 font-medium">Entry</th>
                      <th className="text-right px-4 py-3 font-medium">Current</th>
                      <th className="text-right px-4 py-3 font-medium">P&L</th>
                      <th className="text-left px-4 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((t, i) => {
                      const pnl = t.pnl ?? 0;
                      return (
                        <tr key={t.id || i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                          <td className="px-4 py-3 font-medium">{t.symbol}</td>
                          <td className="px-4 py-3">
                            <span className={`flex items-center gap-1 text-xs font-bold ${
                              t.action === "BUY" ? "text-trade-up" : "text-trade-down"
                            }`}>
                              {t.action === "BUY" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                              {t.action}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-mono">{t.entry_price?.toLocaleString() ?? "—"}</td>
                          <td className="px-4 py-3 text-right font-mono">{t.current_price?.toLocaleString() ?? "—"}</td>
                          <td className={`px-4 py-3 text-right font-mono font-bold ${pnl >= 0 ? "text-trade-up" : "text-trade-down"}`}>
                            {pnl >= 0 ? "+" : ""}{pnl.toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-xs px-2 py-0.5 rounded-full bg-trade-up/15 text-trade-up">{t.status}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
