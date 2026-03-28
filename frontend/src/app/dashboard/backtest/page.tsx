"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { backtestService } from "@/services/api";
import { useSymbols } from "@/hooks/useSymbols";
import type { BacktestResult } from "@/types";
import { cn } from "@/lib/utils";

// rechart components
import {
  ResponsiveContainer,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
} from "recharts";

// shadcn/ui
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

// FontAwesome
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faFlask,
  faPlay,
  faCircleNotch,
  faBolt,
  faBullseye,
  faChartSimple,
  faArrowTrendUp,
  faArrowTrendDown,
  faVial,
  faHistory,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";

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

  const { grouped: symbolGroups, loading: symbolsLoading } = useSymbols();

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    setHasRun(true);
    try {
      const { data } = await backtestService.run(
        symbol,
        period,
        Number(balance),
      );
      setResult(data);
    } catch (err: unknown) {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as {
          response?: { status?: number; data?: { detail?: string } };
        };
        const status = axiosErr.response?.status;
        const detail = axiosErr.response?.data?.detail;
        if (status === 503) {
          setError(
            `⚠️ Model AI belum dilatih untuk simbol ini. Hubungi admin untuk training terlebih dahulu.`,
          );
        } else if (status === 404) {
          setError(`❌ Simbol tidak dikenal atau belum terdaftar di sistem.`);
        } else {
          setError(detail || "Gagal menjalankan backtest");
        }
      } else {
        const msg =
          err instanceof Error ? err.message : "Gagal menjalankan backtest";
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tight">
             Backtest Engine
          </h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            🧪 Strategy simulation on historical data — <span className="text-chart-5 font-black uppercase tracking-widest text-[10px]">Elite Testing</span>
          </p>
        </div>
      </div>

      {/* Input Form Card */}
      <Card className="glass-panel border-white/10 overflow-hidden">
        <CardHeader className="bg-white/5 border-b border-white/5 pb-4 px-6">
           <CardTitle className="text-xs font-black uppercase tracking-[0.2em] text-primary flex items-center gap-2">
              <FontAwesomeIcon icon={faVial as IconProp} className="w-3.5 h-3.5" />
              SIMULATION PARAMETERS
           </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-end">
            <div className="md:col-span-4 space-y-2.5">
              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Symbol Selection</Label>
              <div className="relative group">
                <select
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  disabled={symbolsLoading}
                  className="w-full h-11 px-4 pr-10 rounded-xl bg-white/5 border border-white/10 text-sm font-bold outline-none focus:border-primary/40 transition-all cursor-pointer appearance-none disabled:opacity-50"
                >
                  {symbolsLoading ? (
                    <option>Loading assets...</option>
                  ) : (
                    symbolGroups.map((group) => (
                      <optgroup
                        key={group.group}
                        label={group.group}
                        className="bg-black text-muted-foreground"
                      >
                        {group.options.map((opt) => (
                          <option
                            key={opt.value}
                            value={opt.value}
                            className="bg-black/90 text-foreground"
                          >
                            {opt.flag} {opt.value} — {opt.label.split("–")[1]?.trim() || opt.label}
                          </option>
                        ))}
                      </optgroup>
                    ))
                  )}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground group-focus-within:text-primary transition-colors">
                   <FontAwesomeIcon icon={faTriangleExclamation as IconProp} className="w-3 h-3 rotate-180" />
                </div>
              </div>
            </div>

            <div className="md:col-span-3 space-y-2.5">
              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Period Range</Label>
              <div className="flex gap-1.5 p-1 bg-white/5 border border-white/10 rounded-xl h-11">
                {["6mo", "1y", "2y", "5y"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={cn(
                      "flex-1 rounded-lg text-xs font-black uppercase tracking-tighter transition-all",
                      period === p
                        ? "bg-primary/20 text-primary border border-primary/20 shadow-lg shadow-primary/10"
                        : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                    )}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            <div className="md:col-span-3 space-y-2.5">
              <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Initial Capital (IDR)</Label>
              <Input
                type="number"
                value={balance}
                onChange={(e) => setBalance(e.target.value)}
                className="h-11 bg-white/5 border-white/10 font-mono font-bold focus-visible:ring-primary/20 rounded-xl"
              />
            </div>

            <div className="md:col-span-2">
              <Button
                onClick={runBacktest}
                disabled={loading || !symbol}
                className="w-full h-11 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 font-black tracking-wider gap-2 shadow-lg shadow-emerald-500/5 transition-all"
              >
                {loading ? (
                  <FontAwesomeIcon icon={faCircleNotch as IconProp} spin className="w-3.5 h-3.5" />
                ) : (
                  <FontAwesomeIcon icon={faPlay as IconProp} className="w-3 h-3" />
                )}
                EXECUTE
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
         <Card className="border-trade-down/20 bg-trade-down/5 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-300">
            <CardContent className="py-5 text-trade-down text-sm font-bold flex items-start gap-3">
               <span className="text-xl shrink-0 mt-0.5">⚠️</span>
               <p className="leading-relaxed">{error}</p>
            </CardContent>
         </Card>
      )}

      {/* Loading State Overlay */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-32 gap-6 bg-white/5 border border-white/10 rounded-3xl animate-pulse">
          <div className="relative">
             <div className="w-20 h-20 rounded-full border-4 border-primary/10 border-t-primary animate-spin" />
             <div className="absolute inset-0 flex items-center justify-center text-primary drop-shadow-glow">
                <FontAwesomeIcon icon={faBolt as IconProp} className="w-6 h-6" />
             </div>
          </div>
          <div className="text-center">
            <p className="text-md font-black uppercase tracking-[0.3em] text-foreground mb-1">Processing Dataset</p>
            <p className="text-xs text-muted-foreground font-medium">Simulating {period} of market data for {symbol}...</p>
          </div>
        </div>
      )}

      {/* Result Visualizations */}
      {!loading && result && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
           {/* KPI Cards */}
           <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                { label: "Total Trades", value: result.total_trades ?? 0, icon: faBullseye, color: "text-blue-400", bg: "bg-blue-400/10" },
                { label: "Win Rate", value: `${(result.win_rate ?? 0).toFixed(1)}%`, icon: faChartSimple, color: (result.win_rate ?? 0) >= 50 ? "text-trade-up" : "text-trade-down", bg: (result.win_rate ?? 0) >= 50 ? "bg-trade-up/10" : "bg-trade-down/10" },
                { label: "Net P&L", value: (result.net_pnl ?? 0).toLocaleString(), icon: (result.net_pnl ?? 0) >= 0 ? faArrowTrendUp : faArrowTrendDown, color: (result.net_pnl ?? 0) >= 0 ? "text-trade-up" : "text-trade-down", bg: (result.net_pnl ?? 0) >= 0 ? "bg-trade-up/10" : "bg-trade-down/10" },
                { label: "DRAWDWN", value: `${(result.max_drawdown ?? 0).toFixed(1)}%`, icon: faArrowTrendDown, color: "text-trade-down", bg: "bg-trade-down/10" },
                { label: "Sharpe", value: (result.sharpe_ratio ?? 0).toFixed(2), icon: faBolt, color: (result.sharpe_ratio ?? 0) >= 1 ? "text-chart-4" : "text-muted-foreground", bg: "bg-chart-4/10" },
              ].map((card) => (
                 <Card key={card.label} className="glass-panel border-white/10">
                    <CardContent className="p-4 flex flex-col items-center text-center">
                       <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-3", card.bg)}>
                          <FontAwesomeIcon icon={card.icon as IconProp} className={cn("w-4 h-4", card.color)} />
                       </div>
                       <p className={cn("text-xl font-black tracking-tighter mb-0.5", card.color)}>{card.value}</p>
                       <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{card.label}</p>
                    </CardContent>
                 </Card>
              ))}
           </div>

           {/* Equity & Trades Grid */}
           <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Equity Chart */}
              <Card className="lg:col-span-8 glass-panel border-white/10">
                <CardHeader className="pb-0 px-6 pt-6 flex flex-row items-center justify-between">
                   <div className="flex items-center gap-3">
                      <div className="w-2 h-8 bg-primary rounded-full" />
                      <div>
                         <CardTitle className="text-sm font-black uppercase tracking-widest">Equity Trajectory</CardTitle>
                         <CardDescription className="text-[10px]">{symbol} • {period} Simulation</CardDescription>
                      </div>
                   </div>
                </CardHeader>
                <CardContent className="h-[380px] pt-8">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={result.equity_curve?.map((v, i) => ({ trade: i + 1, equity: v })) || []}
                    >
                      <defs>
                        <linearGradient id="btEqGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                      <XAxis 
                        dataKey="trade" 
                        stroke="rgba(255,255,255,0.1)"
                        tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis 
                        stroke="rgba(255,255,255,0.1)"
                        tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} 
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(10,10,10,0.95)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "12px",
                          fontSize: "12px",
                          backdropFilter: "blur(10px)"
                        }}
                      />
                      <Area type="monotone" dataKey="equity" stroke="var(--primary)" fill="url(#btEqGrad)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Trade Log */}
              <Card className="lg:col-span-4 glass-panel border-white/10 flex flex-col">
                <CardHeader className="bg-white/5 border-b border-white/5 py-4 px-6">
                   <CardTitle className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
                       <FontAwesomeIcon icon={faHistory as IconProp} className="w-3.5 h-3.5 opacity-50" />
                       Execution History
                   </CardTitle>
                </CardHeader>
                <CardContent className="p-0 flex-1 overflow-hidden">
                   <div className="h-full max-h-[400px] overflow-y-auto">
                      <Table>
                        <TableHeader className="bg-white/5 sticky top-0">
                          <TableRow className="border-white/10 hover:bg-transparent">
                            <TableHead className="font-black text-[9px] uppercase tracking-widest h-10">#</TableHead>
                            <TableHead className="font-black text-[9px] uppercase tracking-widest h-10 text-center">SIDE</TableHead>
                            <TableHead className="font-black text-[9px] uppercase tracking-widest h-10 text-right">EXIT</TableHead>
                            <TableHead className="font-black text-[9px] uppercase tracking-widest h-10 text-right px-6">P&L</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {result.trades?.map((t, i) => (
                            <TableRow key={i} className="border-white/5 hover:bg-white/5 group h-12">
                              <TableCell className="text-[10px] font-mono text-muted-foreground opacity-50">{i + 1}</TableCell>
                              <TableCell className="text-center">
                                <Badge className={cn(
                                   "font-black text-[9px] px-1.5 py-0 border-none",
                                   t.action === "BUY" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                                )}>
                                   {t.action}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right font-mono text-[11px] font-bold">
                                {t.exit_price?.toLocaleString() ?? "—"}
                              </TableCell>
                              <TableCell className={cn("text-right font-mono font-black text-[11px] px-6", (t.pnl ?? 0) >= 0 ? "text-trade-up" : "text-trade-down")}>
                                {(t.pnl ?? 0) >= 0 ? "+" : ""}{(t.pnl ?? 0).toLocaleString()}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                   </div>
                </CardContent>
              </Card>
           </div>
        </div>
      )}

      {/* Initial/Empty State */}
      {!loading && !result && (
        <Card className="glass-panel border-white/5 py-32 rounded-3xl flex flex-col items-center justify-center border-dashed border-2">
           <div className="w-16 h-16 rounded-3xl bg-white/5 flex items-center justify-center text-muted-foreground mb-6">
              <FontAwesomeIcon icon={faFlask as IconProp} className="w-8 h-8 opacity-20" />
           </div>
           <div className="text-center max-w-sm px-6">
              <h3 className="text-lg font-black uppercase tracking-tighter mb-2">Backtest Engine Ready</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                 Configure your target symbol and initial capital on the top panel to begin simulation. 
                 AI Hub will run 2,000+ iterations across historical data.
              </p>
              {!hasRun && (
                 <Button variant="outline" onClick={runBacktest} className="mt-8 border-white/10 font-black text-[10px] tracking-widest uppercase">
                    Initialize Simulation
                 </Button>
              )}
           </div>
        </Card>
      )}
    </div>
  );
}
