"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { portfolioService, dashboardService } from "@/services/api";
import type { OpenTrade } from "@/types";
import { cn } from "@/lib/utils";

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
  faWallet,
  faArrowUp,
  faArrowDown,
  faCircleNotch,
  faPaperPlane,
  faChartLine,
  faRotate,
  faBoxOpen,
  faMoneyBillTrendUp,
  faBuildingColumns,
  faHistory,
} from "@fortawesome/free-solid-svg-icons";

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
      setOrderResult(`✅ Success: ${orderAction} ${orderQty} lot ${orderSymbol.toUpperCase()} at ${Number(orderPrice).toLocaleString()}`);
      setOrderSymbol("");
      setOrderQty("");
      setOrderPrice("");
      fetchTrades();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Order execution failed";
      setOrderError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const totalPnl = trades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);

  if (!isAuthenticated) return null;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tight">
             Virtual Portfolio
          </h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            💼 Virtual trading simulator — <span className="text-chart-5 font-black uppercase tracking-widest text-[10px]">Active Session</span>
          </p>
        </div>
        
        <Button 
          variant="outline" 
          onClick={fetchTrades} 
          disabled={loading}
          className="glass-panel border-white/10 font-black text-[10px] tracking-widest uppercase h-9 gap-2"
        >
          <FontAwesomeIcon icon={faRotate as IconProp} className={cn("w-3 h-3", loading && "animate-spin")} />
          Sync Data
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Form & Summary */}
        <div className="lg:col-span-4 space-y-6">
          {/* Order Form */}
          <Card className="glass-panel border-white/10 overflow-hidden">
            <CardHeader className="bg-white/5 border-b border-white/10 pb-4 px-6">
               <CardTitle className="text-xs font-black uppercase tracking-[0.2em] text-primary flex items-center gap-2">
                  <FontAwesomeIcon icon={faMoneyBillTrendUp as IconProp} className="w-3.5 h-3.5" />
                  NEW VIRTUAL ORDER
               </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {/* Buy/Sell Tabs */}
              <div className="grid grid-cols-2 gap-2 p-1 bg-white/5 border border-white/10 rounded-xl">
                <Button
                  onClick={() => setOrderAction("BUY")}
                  variant="ghost"
                  className={cn(
                    "h-10 font-black text-xs tracking-widest rounded-lg transition-all",
                    orderAction === "BUY" 
                      ? "bg-trade-up/10 text-trade-up border border-trade-up/20 shadow-lg shadow-trade-up/5" 
                      : "text-muted-foreground hover:bg-white/5"
                  )}
                >
                  <FontAwesomeIcon icon={faArrowUp as IconProp} className="mr-2 text-[10px]" />
                  BUY
                </Button>
                <Button
                  onClick={() => setOrderAction("SELL")}
                  variant="ghost"
                  className={cn(
                    "h-10 font-black text-xs tracking-widest rounded-lg transition-all",
                    orderAction === "SELL" 
                      ? "bg-trade-down/10 text-trade-down border border-trade-down/20 shadow-lg shadow-trade-down/5" 
                      : "text-muted-foreground hover:bg-white/5"
                  )}
                >
                  <FontAwesomeIcon icon={faArrowDown as IconProp} className="mr-2 text-[10px]" />
                  SELL
                </Button>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Asset Symbol</Label>
                  <Input
                    value={orderSymbol}
                    onChange={(e) => setOrderSymbol(e.target.value)}
                    placeholder="e.g. BBCA.JK"
                    className="bg-white/5 border-white/10 focus-visible:ring-primary/20 h-11 font-bold uppercase placeholder:lowercase placeholder:font-normal"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Lot Size</Label>
                    <Input
                      type="number"
                      value={orderQty}
                      onChange={(e) => setOrderQty(e.target.value)}
                      placeholder="qty"
                      className="bg-white/5 border-white/10 focus-visible:ring-primary/20 h-11 font-mono font-bold"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Price (IDR)</Label>
                    <Input
                      type="number"
                      value={orderPrice}
                      onChange={(e) => setOrderPrice(e.target.value)}
                      placeholder="price"
                      className="bg-white/5 border-white/10 focus-visible:ring-primary/20 h-11 font-mono font-bold"
                    />
                  </div>
                </div>
              </div>

              <Button
                onClick={executeOrder}
                disabled={submitting || !orderSymbol || !orderQty || !orderPrice}
                className={cn(
                  "w-full h-12 font-black tracking-[0.2em] shadow-lg transition-all",
                  orderAction === "BUY" 
                    ? "bg-trade-up/10 text-trade-up border border-trade-up/20 hover:bg-trade-up/20 shadow-trade-up/5" 
                    : "bg-trade-down/10 text-trade-down border border-trade-down/20 hover:bg-trade-down/20 shadow-trade-down/5"
                )}
              >
                {submitting ? (
                  <FontAwesomeIcon icon={faCircleNotch as IconProp} spin className="w-4 h-4" />
                ) : (
                  <>
                    <FontAwesomeIcon icon={faPaperPlane as IconProp} className="mr-2 w-3.5 h-3.5" />
                    EXECUTE {orderAction}
                  </>
                )}
              </Button>

              {orderResult && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[11px] font-bold text-emerald-400 animate-in zoom-in-95 duration-200">
                   {orderResult}
                </div>
              )}
              {orderError && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-[11px] font-bold text-red-400 animate-in zoom-in-95 duration-200">
                   {orderError}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Account Summary */}
          <Card className="glass-panel border-white/10 overflow-hidden">
            <CardHeader className="bg-white/5 border-b border-white/10 py-3 px-6">
              <CardTitle className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Portfolio Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
               <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground flex items-center gap-2">
                     <FontAwesomeIcon icon={faBoxOpen as IconProp} className="w-3 h-3 opacity-30" />
                     Open Positions
                  </span>
                  <span className="font-mono font-black">{trades.length}</span>
               </div>
               <div className="h-px bg-white/5 w-full" />
               <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground flex items-center gap-2">
                     <FontAwesomeIcon icon={faChartLine as IconProp} className="w-3 h-3 opacity-30" />
                     Unrealized P&L
                  </span>
                  <span className={cn("font-mono font-black text-sm", totalPnl >= 0 ? "text-trade-up" : "text-trade-down")}>
                     {totalPnl >= 0 ? "+" : ""}{totalPnl.toLocaleString()}
                  </span>
               </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Active Positions */}
        <div className="lg:col-span-8">
           <Card className="glass-panel border-white/10 flex flex-col h-full min-h-[600px]">
              <CardHeader className="bg-white/5 border-b border-white/10 py-4 px-6 flex flex-row items-center justify-between">
                 <div className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    <CardTitle className="text-sm font-black uppercase tracking-widest">Active Positions</CardTitle>
                 </div>
                 <Badge variant="outline" className="border-white/10 text-[9px] font-black tracking-widest text-muted-foreground">
                    REALTIME TRACKING
                 </Badge>
              </CardHeader>
              <CardContent className="p-0 flex-1 overflow-hidden relative">
                {loading ? (
                   <div className="absolute inset-0 flex items-center justify-center bg-black/10 backdrop-blur-[2px] z-10 animate-in fade-in">
                      <FontAwesomeIcon icon={faCircleNotch as IconProp} spin className="w-10 h-10 text-primary opacity-40" />
                   </div>
                ) : trades.length === 0 ? (
                   <div className="h-full flex flex-col items-center justify-center py-32 opacity-30 px-12 text-center">
                      <FontAwesomeIcon icon={faWallet as IconProp} className="w-16 h-16 mb-6" />
                      <p className="font-black uppercase tracking-widest text-xs">No active exposures detected</p>
                      <p className="text-[10px] mt-1 font-medium italic">Simulate market orders on the left panel to build your index.</p>
                   </div>
                ) : (
                   <div className="overflow-x-auto">
                      <Table>
                        <TableHeader className="bg-white/5 border-b border-white/5">
                          <TableRow className="border-white/10 hover:bg-transparent">
                            <TableHead className="font-black text-[10px] uppercase tracking-widest h-11 px-6">ASSET</TableHead>
                            <TableHead className="font-black text-[10px] uppercase tracking-widest h-11">SIDE</TableHead>
                            <TableHead className="font-black text-[10px] uppercase tracking-widest h-11 text-right">ENTRY</TableHead>
                            <TableHead className="font-black text-[10px] uppercase tracking-widest h-11 text-right">MARK</TableHead>
                            <TableHead className="font-black text-[10px] uppercase tracking-widest h-11 text-right px-6">P&L (NET)</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {trades.map((t, i) => {
                            const pnl = t.pnl ?? 0;
                            return (
                              <TableRow key={t.id || i} className="border-white/5 hover:bg-white/5 group h-14">
                                <TableCell className="px-6">
                                   <div className="flex items-center gap-3">
                                      <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center pointer-events-none border border-white/5">
                                         <FontAwesomeIcon icon={faBuildingColumns as IconProp} className="text-[10px] opacity-20" />
                                      </div>
                                      <div className="flex flex-col">
                                         <span className="font-black text-sm tracking-tight">{t.symbol}</span>
                                         <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground opacity-50">VIRTUAL</span>
                                      </div>
                                   </div>
                                </TableCell>
                                <TableCell>
                                   <Badge className={cn(
                                      "font-black text-[9px] px-2 py-0.5 border-none shadow-sm",
                                      t.action === "BUY" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                                   )}>
                                      {t.action}
                                   </Badge>
                                </TableCell>
                                <TableCell className="text-right font-mono text-[11px] font-bold opacity-60">
                                   {t.entry_price?.toLocaleString() ?? "—"}
                                </TableCell>
                                <TableCell className="text-right font-mono text-[11px] font-bold">
                                   {t.current_price?.toLocaleString() ?? "—"}
                                </TableCell>
                                <TableCell className="text-right px-6">
                                   <div className="flex flex-col items-end">
                                      <span className={cn("font-mono font-black text-sm", pnl >= 0 ? "text-trade-up" : "text-trade-down")}>
                                         {pnl >= 0 ? "+" : ""}{pnl.toLocaleString()}
                                      </span>
                                      <span className="text-[9px] font-black opacity-20 uppercase">POSITION ID: {t.id?.slice(-6) || "SIM"}</span>
                                   </div>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                   </div>
                )}
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
}
