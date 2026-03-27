"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { marketService, searchService } from "@/services/api";
import type {
  ChartCandle,
  CryptoSummary,
  BandarSummary,
  ForexSummary,
  SearchResult,
} from "@/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
} from "recharts";
import {
  Search,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  Globe,
  ArrowUpCircle,
  ArrowDownCircle,
  Loader2,
} from "lucide-react";

export default function MarketPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"chart" | "crypto" | "forex" | "bandar">("chart");

  // Chart state
  const [symbol, setSymbol] = useState("BBCA.JK");
  const [timeframe, setTimeframe] = useState("1h");
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [chartLoading, setChartLoading] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showSearch, setShowSearch] = useState(false);

  // Market data states
  const [cryptoData, setCryptoData] = useState<CryptoSummary | null>(null);
  const [bandarData, setBandarData] = useState<BandarSummary | null>(null);
  const [forexData, setForexData] = useState<ForexSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  // Search handler
  const handleSearch = useCallback(async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    try {
      const { data } = await searchService.search(q);
      setSearchResults(data);
      setShowSearch(true);
    } catch {
      setSearchResults([]);
    }
  }, []);

  // Chart data fetch
  const fetchChart = useCallback(async () => {
    setChartLoading(true);
    setError(null);
    try {
      const { data } = await marketService.getChart(symbol, timeframe);
      setChartData(data.data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal memuat chart";
      setError(msg);
    } finally {
      setChartLoading(false);
    }
  }, [symbol, timeframe]);

  // Crypto data fetch
  const fetchCrypto = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await marketService.getCryptoSummary();
      setCryptoData(data);
    } catch {
      setCryptoData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Bandar data fetch
  const fetchBandar = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await marketService.getBandar(symbol);
      setBandarData(data);
    } catch {
      setBandarData(null);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  // Forex data fetch
  const fetchForex = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await marketService.getForexSummary();
      setForexData(data);
    } catch {
      setForexData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (activeTab === "chart") fetchChart();
    else if (activeTab === "crypto") fetchCrypto();
    else if (activeTab === "bandar") fetchBandar();
    else if (activeTab === "forex") fetchForex();
  }, [activeTab, isAuthenticated, fetchChart, fetchCrypto, fetchBandar, fetchForex]);

  const selectSymbol = (s: string) => {
    setSymbol(s);
    setShowSearch(false);
    setSearchQuery("");
    setActiveTab("chart");
  };

  const tabs = [
    { key: "chart" as const, label: "Chart", icon: BarChart3 },
    { key: "crypto" as const, label: "Crypto", icon: Activity },
    { key: "forex" as const, label: "Forex", icon: Globe },
    { key: "bandar" as const, label: "Bandar", icon: TrendingUp },
  ];

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
              Market Data
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              📊 Analisis pasar real-time — <span className="text-chart-5 font-japanese">マーケット</span>
            </p>
          </div>

          {/* Search Bar */}
          <div className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Cari simbol (BBCA, BTC, USD...)"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowSearch(true)}
              onBlur={() => setTimeout(() => setShowSearch(false), 200)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all outline-none"
            />
            {showSearch && searchResults.length > 0 && (
              <div className="absolute top-full mt-1 left-0 right-0 z-50 glass-panel rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                {searchResults.map((r) => (
                  <button
                    key={r.symbol}
                    onMouseDown={() => selectSymbol(r.symbol)}
                    className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/10 transition-colors text-left cursor-pointer"
                  >
                    <div>
                      <span className="text-sm font-medium">{r.symbol}</span>
                      <span className="text-xs text-muted-foreground ml-2">{r.category} · {r.type}</span>
                    </div>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        r.status === "BUY"
                          ? "bg-trade-up/20 text-trade-up"
                          : r.status === "SELL"
                          ? "bg-trade-down/20 text-trade-down"
                          : "bg-white/10 text-muted-foreground"
                      }`}
                    >
                      {r.status}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-6 p-1 glass-panel rounded-xl w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                activeTab === tab.key
                  ? "bg-primary/20 text-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === "chart" && (
          <div className="space-y-4">
            {/* Symbol & Timeframe Controls */}
            <div className="flex items-center gap-4 glass-panel rounded-xl p-4">
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-primary">{symbol}</span>
                {chartData.length > 0 && (
                  <span className={`text-sm font-medium ${
                    chartData[chartData.length - 1]?.close >= chartData[0]?.close
                      ? "text-trade-up" : "text-trade-down"
                  }`}>
                    {chartData[chartData.length - 1]?.close?.toFixed(2)}
                  </span>
                )}
              </div>
              <div className="ml-auto flex gap-1">
                {["15m", "1h", "1d"].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`px-3 py-1 rounded text-xs font-medium transition-all cursor-pointer ${
                      timeframe === tf
                        ? "bg-primary/20 text-primary"
                        : "text-muted-foreground hover:bg-white/10"
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            {/* Price Chart */}
            <div className="glass-panel rounded-xl p-6" style={{ height: 400 }}>
              {chartLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full text-trade-down text-sm">
                  {error}
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--trade-up)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="var(--trade-up)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis
                      dataKey="time"
                      tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }}
                      tickFormatter={(v) => {
                        try { return new Date(v).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }); }
                        catch { return v; }
                      }}
                    />
                    <YAxis
                      domain={["auto", "auto"]}
                      tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(0,0,0,0.8)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="close"
                      stroke="var(--trade-up)"
                      fill="url(#priceGrad)"
                      strokeWidth={2}
                    />
                    <Line type="monotone" dataKey="sma20" stroke="var(--chart-4)" strokeWidth={1} dot={false} />
                    <Line type="monotone" dataKey="sma50" stroke="var(--chart-5)" strokeWidth={1} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Volume + RSI Panel */}
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel rounded-xl p-4" style={{ height: 200 }}>
                <p className="text-xs text-muted-foreground mb-2 font-medium">Volume</p>
                <ResponsiveContainer width="100%" height="85%">
                  <BarChart data={chartData.slice(-60)}>
                    <Bar dataKey="volume" fill="var(--chart-3)" opacity={0.6} radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="glass-panel rounded-xl p-4" style={{ height: 200 }}>
                <p className="text-xs text-muted-foreground mb-2 font-medium">RSI (14)</p>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={chartData.slice(-60)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} />
                    <Line type="monotone" dataKey="rsi" stroke="var(--chart-4)" strokeWidth={1.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeTab === "crypto" && (
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : cryptoData ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Fear & Greed */}
                <div className="glass-panel rounded-xl p-6 text-center">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3">Fear & Greed Index</p>
                  <div className="relative w-32 h-32 mx-auto">
                    <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                      <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                      <circle
                        cx="50" cy="50" r="40" fill="none"
                        stroke={cryptoData.fear_greed > 60 ? "var(--trade-up)" : cryptoData.fear_greed < 40 ? "var(--trade-down)" : "var(--chart-4)"}
                        strokeWidth="8"
                        strokeDasharray={`${(cryptoData.fear_greed / 100) * 251.2} 251.2`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-3xl font-bold">{cryptoData.fear_greed}</span>
                    </div>
                  </div>
                  <p className="mt-2 text-sm font-medium">
                    {cryptoData.fear_greed > 70 ? "Extreme Greed 🤑" : cryptoData.fear_greed > 50 ? "Greed" : cryptoData.fear_greed > 30 ? "Fear" : "Extreme Fear 😱"}
                  </p>
                </div>

                {/* Net Flow */}
                <div className="glass-panel rounded-xl p-6">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3">Whale Net Flow</p>
                  <p className="text-3xl font-bold text-trade-up">{cryptoData.net_flow}</p>
                  <p className="text-sm text-muted-foreground mt-1">{cryptoData.symbol}</p>
                  <div className="mt-4 flex items-center gap-2">
                    {cryptoData.action === "BUY" ? (
                      <ArrowUpCircle className="w-5 h-5 text-trade-up" />
                    ) : (
                      <ArrowDownCircle className="w-5 h-5 text-trade-down" />
                    )}
                    <span className={`text-sm font-bold ${cryptoData.action === "BUY" ? "text-trade-up" : "text-trade-down"}`}>
                      {cryptoData.action}
                    </span>
                  </div>
                </div>

                {/* Score */}
                <div className="glass-panel rounded-xl p-6">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3">Whale Score</p>
                  <p className={`text-4xl font-bold ${cryptoData.score > 0 ? "text-trade-up" : "text-trade-down"}`}>
                    {cryptoData.score}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">Exchange: {cryptoData.exchange || "N/A"}</p>
                </div>
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-10">Tidak ada data crypto.</p>
            )}
          </div>
        )}

        {activeTab === "forex" && (
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : forexData ? (
              <div className="glass-panel rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold">{forexData.pair}</h2>
                    <p className="text-sm text-muted-foreground">Session: {forexData.session || "N/A"}</p>
                  </div>
                  <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                    forexData.signal === "BUY" ? "bg-trade-up/20 text-trade-up"
                    : forexData.signal === "SELL" ? "bg-trade-down/20 text-trade-down"
                    : "bg-white/10 text-muted-foreground"
                  }`}>
                    {forexData.signal}
                  </span>
                </div>

                {/* Strength Meter */}
                <h3 className="text-sm font-medium text-muted-foreground mb-4">Currency Strength</h3>
                <div className="space-y-3">
                  {Object.entries(forexData.strength || {}).sort((a, b) => (b[1] as number) - (a[1] as number)).map(([currency, value]) => (
                    <div key={currency} className="flex items-center gap-3">
                      <span className="text-sm font-mono w-8">{currency}</span>
                      <div className="flex-1 h-3 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.max(5, Math.min(100, ((value as number) + 100) / 2))}%`,
                            background: (value as number) > 0
                              ? "linear-gradient(90deg, var(--trade-up), rgba(0,255,100,0.5))"
                              : "linear-gradient(90deg, var(--trade-down), rgba(255,50,50,0.5))",
                          }}
                        />
                      </div>
                      <span className={`text-xs font-mono w-12 text-right ${(value as number) > 0 ? "text-trade-up" : "text-trade-down"}`}>
                        {(value as number).toFixed(1)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-10">Tidak ada data forex.</p>
            )}
          </div>
        )}

        {activeTab === "bandar" && (
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : bandarData ? (
              <div className="glass-panel rounded-xl p-6">
                <div className="flex items-center gap-4 mb-6">
                  <h2 className="text-xl font-bold">{bandarData.symbol}</h2>
                  <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                    bandarData.status.includes("ACCUM") ? "bg-trade-up/20 text-trade-up"
                    : bandarData.status.includes("DISTRIB") ? "bg-trade-down/20 text-trade-down"
                    : "bg-white/10 text-muted-foreground"
                  }`}>
                    {bandarData.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 rounded-lg bg-white/5">
                    <p className="text-xs text-muted-foreground mb-1">Score</p>
                    <p className={`text-2xl font-bold ${bandarData.score > 0 ? "text-trade-up" : "text-trade-down"}`}>
                      {bandarData.score}
                    </p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-white/5">
                    <p className="text-xs text-muted-foreground mb-1">Vol Ratio</p>
                    <p className="text-2xl font-bold">{bandarData.vol_ratio?.toFixed(2)}</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-white/5">
                    <p className="text-xs text-muted-foreground mb-1">Status</p>
                    <p className="text-lg font-bold">{bandarData.status}</p>
                  </div>
                </div>

                <p className="mt-4 text-sm text-muted-foreground">{bandarData.message}</p>
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-10">Tidak ada data bandarmology.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
