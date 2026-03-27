"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import type { DashboardResponse, SignalItem } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  AlertCircle,
  BarChart3,
  Loader2,
} from "lucide-react";

const PIE_COLORS = [
  "oklch(0.75 0.15 150)",   // green (BUY)
  "oklch(0.6 0.2 20)",      // red (SELL)
  "oklch(0.7 0.15 300)",    // purple (HOLD)
  "oklch(0.8 0.15 70)",     // golden (OTHER)
];

function ActionBadge({ action }: { action: string }) {
  const upper = action?.toUpperCase() ?? "HOLD";
  const config: Record<string, { icon: React.ElementType; cls: string }> = {
    BUY: { icon: TrendingUp, cls: "text-trade-up bg-trade-up/10 border-trade-up/30" },
    SELL: { icon: TrendingDown, cls: "text-trade-down bg-trade-down/10 border-trade-down/30" },
    HOLD: { icon: Minus, cls: "text-chart-5 bg-chart-5/10 border-chart-5/30" },
  };
  const c = config[upper] ?? config.HOLD;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold border ${c.cls}`}>
      <Icon className="w-3 h-3" />
      {upper}
    </span>
  );
}

export function DashboardOverview() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const res = await api.get<DashboardResponse>("/dashboard/all");
        setData(res.data);
        setError("");
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Gagal memuat data dashboard";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000); // polling 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="ml-3 text-muted-foreground animate-pulse">
          Memuat data neural engine...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="glass-panel border-trade-down/30">
        <CardContent className="flex items-center gap-3 py-6">
          <AlertCircle className="w-6 h-6 text-trade-down" />
          <div>
            <p className="text-sm font-medium text-trade-down">Koneksi gagal</p>
            <p className="text-xs text-muted-foreground">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const { signals, open_trades } = data;

  const pieData = [
    { name: "BUY", value: signals.counts.BUY },
    { name: "SELL", value: signals.counts.SELL },
    { name: "HOLD", value: signals.counts.HOLD },
    { name: "OTHER", value: signals.counts.OTHER },
  ].filter((d) => d.value > 0);

  // Bar chart: Top 8 signals by confidence
  const barData = signals.items
    .filter((s: SignalItem) => s.Confidence != null)
    .slice(0, 8)
    .map((s: SignalItem) => ({
      symbol: s.symbol,
      confidence: Number(((s.Confidence ?? 0) * 100).toFixed(1)),
      action: s.Action ?? "HOLD",
    }));

  const statCards = [
    {
      label: "Total Signals",
      value: signals.total,
      icon: Activity,
      color: "text-primary",
      glow: "shadow-primary/20",
    },
    {
      label: "BUY",
      value: signals.counts.BUY,
      icon: TrendingUp,
      color: "text-trade-up",
      glow: "shadow-trade-up/20",
    },
    {
      label: "SELL",
      value: signals.counts.SELL,
      icon: TrendingDown,
      color: "text-trade-down",
      glow: "shadow-trade-down/20",
    },
    {
      label: "HOLD",
      value: signals.counts.HOLD,
      icon: Minus,
      color: "text-chart-5",
      glow: "shadow-chart-5/20",
    },
  ];

  return (
    <div className="space-y-6">
      {/* ─── Stats Grid ─── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <Card key={card.label} className={`glass-panel group overflow-hidden relative hover:shadow-lg ${card.glow} transition-all duration-300`}>
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-white/5 to-transparent" />
            <CardContent className="flex items-center gap-4 p-5">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-white/5 ${card.color}`}>
                <card.icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                  {card.label}
                </p>
                <p className={`text-2xl font-bold ${card.color}`}>
                  {card.value}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ─── Charts Row ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Pie Chart */}
        <Card className="glass-panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" />
              Signal Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "oklch(0.18 0.005 285)",
                    border: "1px solid oklch(0.3 0.006 286)",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center gap-4 mt-2">
              {pieData.map((item, i) => (
                <div key={item.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i] }} />
                  {item.name}: {item.value}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Bar Chart: Top Confidence */}
        <Card className="glass-panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-chart-4" />
              Top Confidence Signals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={barData} layout="vertical" barSize={14}>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.3 0.006 286)" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: "oklch(0.7 0 0)", fontSize: 11 }} />
                <YAxis dataKey="symbol" type="category" width={70} tick={{ fill: "oklch(0.7 0 0)", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "oklch(0.18 0.005 285)",
                    border: "1px solid oklch(0.3 0.006 286)",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                  formatter={(value) => [`${value}%`, "Confidence"]}
                />
                <Bar dataKey="confidence" radius={[0, 4, 4, 0]} fill="oklch(0.6 0.118 284.53)" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* ─── Open Trades Table ─── */}
      <Card className="glass-panel">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Activity className="w-4 h-4 text-trade-up" />
            Open Trades
            <span className="ml-auto text-xs text-muted-foreground font-normal">
              Last 10 positions
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {open_trades.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Belum ada posisi terbuka saat ini.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="text-xs">Symbol</TableHead>
                  <TableHead className="text-xs">Action</TableHead>
                  <TableHead className="text-xs text-right">Entry Price</TableHead>
                  <TableHead className="text-xs text-right">Current</TableHead>
                  <TableHead className="text-xs text-right">PnL</TableHead>
                  <TableHead className="text-xs text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {open_trades.map((trade, i) => (
                  <TableRow key={trade.id ?? i} className="border-white/5 hover:bg-white/5">
                    <TableCell className="font-mono font-medium text-xs">{trade.symbol}</TableCell>
                    <TableCell>
                      <ActionBadge action={trade.action} />
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {trade.entry_price?.toFixed(4) ?? "—"}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {trade.current_price?.toFixed(4) ?? "—"}
                    </TableCell>
                    <TableCell className={`text-right font-mono text-xs font-bold ${(trade.pnl ?? 0) >= 0 ? "text-trade-up" : "text-trade-down"}`}>
                      {trade.pnl != null ? `${trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}%` : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-trade-up/10 text-trade-up border border-trade-up/20 font-medium">
                        {trade.status}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
