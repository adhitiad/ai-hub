"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { marketService, searchService, assetsService, type AssetFromDB } from "@/services/api";
import { cn } from "@/lib/utils";
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
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faMagnifyingGlass,
  faArrowTrendUp,
  faChartSimple,
  faHeartbeat,
  faEarthAmericas,
  faCircleArrowUp,
  faCircleArrowDown,
  faSpinner,
  faChevronLeft,
  faChevronRight,
  faLayerGroup,
  faBolt,
  faCircleInfo
} from "@fortawesome/free-solid-svg-icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CryptoSummary, ForexSummary, BandarSummary, ChartCandle, SearchResult } from "@/types";

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

  // Pagination states
  const [assetList, setAssetList] = useState<AssetFromDB[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
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
      const { data } = await marketService.getForexSummary(symbol);
      setForexData(data);
    } catch {
      setForexData(null);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  const fetchAssetsByCategory = useCallback(async (category: string) => {
    try {
      const { data } = await assetsService.list(category);
      setAssetList(data.assets || []);
      setCurrentPage(1);
    } catch (err) {
      console.error("Gagal memuat daftar aset:", err);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (activeTab === "chart") fetchChart();
    else if (activeTab === "crypto") {
      fetchCrypto();
      fetchAssetsByCategory("CRYPTO");
    } else if (activeTab === "bandar") {
      fetchBandar();
      fetchAssetsByCategory("STOCKS_INDO");
    } else if (activeTab === "forex") {
      fetchForex();
      fetchAssetsByCategory("FOREX");
    }
  }, [activeTab, isAuthenticated, fetchChart, fetchCrypto, fetchBandar, fetchForex, fetchAssetsByCategory]);

  const paginatedAssets = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return assetList.slice(start, start + itemsPerPage);
  }, [assetList, currentPage]);

  const totalPages = Math.ceil(assetList.length / itemsPerPage);

  const PaginatedAssetTable = () => (
    <Card className="mt-8 bg-card/50 backdrop-blur-sm border-border/50 shadow-2xl overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-3 bg-accent/20 border-b border-border/50 space-y-0">
        <div className="flex flex-col gap-1">
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <FontAwesomeIcon icon={faLayerGroup as IconProp} className="w-4 h-4 text-primary" /> 
            DAFTAR ASET {activeTab.toUpperCase()}
          </CardTitle>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-black">
            Halaman {currentPage} dari {totalPages || 1}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost" 
            size="icon"
            className="h-8 w-8 hover:bg-white/10"
            disabled={currentPage === 1}
            onClick={(e) => { e.stopPropagation(); setCurrentPage(p => Math.max(1, p - 1)); }}
          >
            <FontAwesomeIcon icon={faChevronLeft as IconProp} className="w-3.5 h-3.5" />
          </Button>
          <div className="text-[10px] bg-primary/20 text-primary border border-primary/20 px-2.5 py-1 rounded font-black">
            {currentPage}
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 hover:bg-accent"
            disabled={currentPage >= totalPages}
            onClick={(e) => { e.stopPropagation(); setCurrentPage(p => Math.min(totalPages, p + 1)); }}
          >
            <FontAwesomeIcon icon={faChevronRight as IconProp} className="w-3.5 h-3.5" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <Table>
          <TableHeader className="bg-accent/10">
            <TableRow className="border-border/50 hover:bg-transparent uppercase">
              <TableHead className="px-4 py-3 font-black text-[10px] text-muted-foreground">SYMBOL</TableHead>
              <TableHead className="px-4 py-3 font-black text-[10px] text-muted-foreground">CATEGORY</TableHead>
              <TableHead className="px-4 py-3 font-black text-[10px] text-muted-foreground">TYPE</TableHead>
              <TableHead className="px-4 py-3 font-black text-right text-[10px] text-muted-foreground">ACTION</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedAssets.map((asset, i) => (
              <TableRow
                key={`${asset.symbol}-${i}`}
                className={cn(
                  "border-border/50 hover:bg-accent/50 transition-all cursor-pointer group",
                  asset.symbol === symbol && "bg-primary/10 border-l-2 border-l-primary"
                )}
                onClick={() => {
                  setSymbol(asset.symbol);
                  if (activeTab === "crypto") fetchCrypto();
                  else if (activeTab === "forex") fetchForex();
                  else if (activeTab === "bandar") fetchBandar();
                }}
              >
                <TableCell className="px-4 py-3 font-bold tracking-tight">{asset.symbol}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-[10px] border-border bg-accent/20 text-muted-foreground font-black">
                    {asset.category}
                  </Badge>
                </TableCell>
                <TableCell className="text-[10px] text-muted-foreground/60 font-black uppercase tracking-widest">{asset.type}</TableCell>
                <TableCell className="text-right px-4">
                  <Badge className={cn(
                    "text-[10px] font-black px-3 py-1",
                    asset.symbol === symbol ? "bg-primary text-primary-foreground" : "bg-accent text-muted-foreground group-hover:bg-primary/20 group-hover:text-primary transition-colors"
                  )}>
                    {asset.symbol === symbol ? "ACTIVE" : "SELECT"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
            {assetList.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="h-60 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-8 h-8 text-primary opacity-50" />
                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-black italic">Sinkronisasi data pasar...</span>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );

  const selectSymbol = (s: string) => {
    setSymbol(s);
    setShowSearch(false);
    setSearchQuery("");
    setActiveTab("chart");
  };

  const tabs: { key: "chart" | "crypto" | "forex" | "bandar", label: string, icon: IconProp }[] = [
    { key: "chart", label: "Chart", icon: faChartSimple as IconProp },
    { key: "crypto", label: "Crypto", icon: faHeartbeat as IconProp },
    { key: "forex", label: "Forex", icon: faEarthAmericas as IconProp },
    { key: "bandar", label: "Bandar", icon: faArrowTrendUp as IconProp },
  ];

  if (!isAuthenticated) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between py-5 border-b border-border/50">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-500 to-purple-600 bg-clip-text text-transparent uppercase tracking-tighter">
            Pasar Global
          </h1>
          <p className="text-[10px] text-muted-foreground tracking-[0.2em] font-black uppercase mt-1">
            📊 Real-Time Market Analysis · <span className="text-primary">Elite Terminal</span>
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-80 group">
          <FontAwesomeIcon icon={faMagnifyingGlass as IconProp} className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground group-focus-within:text-primary transition-colors z-10" />
          <Input
            type="text"
            placeholder="Cari BBCA, BTC, USD..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowSearch(true)}
            onBlur={() => setTimeout(() => setShowSearch(false), 200)}
            className="pl-10 h-11 bg-card/50 border-border/50 rounded-xl focus-visible:ring-primary/20 focus-visible:border-primary/50 transition-all font-black text-xs uppercase tracking-tight"
          />
          {showSearch && searchResults.length > 0 && (
            <div className="absolute top-full mt-2 left-0 right-0 z-50 bg-card/95 backdrop-blur-xl rounded-xl border border-border shadow-2xl max-h-80 overflow-y-auto">
              {searchResults.map((r) => (
                <button
                  key={r.symbol}
                  onMouseDown={() => selectSymbol(r.symbol)}
                  className="w-full flex items-center justify-between px-4 py-4 hover:bg-accent transition-colors text-left cursor-pointer border-b border-border/50 last:border-0"
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-black tracking-tight">{r.symbol}</span>
                    <span className="text-[10px] text-muted-foreground/60 uppercase font-black tracking-widest">{r.category} · {r.type}</span>
                  </div>
                  <Badge
                    className={cn(
                      "text-[10px] font-black px-3 py-1 rounded-full",
                      r.status === "BUY" ? "bg-emerald-500/20 text-emerald-500"
                      : r.status === "SELL" ? "bg-red-500/20 text-red-500"
                      : "bg-accent text-muted-foreground"
                    )}
                  >
                    {r.status}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </div>
      </header>

        {/* Tabs System */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="w-full mb-8">
          <TabsList className="bg-muted border border-border/50 p-1.5 h-12 rounded-xl flex gap-1">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.key}
                value={tab.key}
                className="flex-1 flex items-center justify-center gap-3 px-6 rounded-lg text-sm font-black transition-all data-[state=active]:bg-card data-[state=active]:text-primary data-[state=active]:shadow-lg cursor-pointer h-full uppercase tracking-tighter"
              >
                <FontAwesomeIcon icon={tab.icon} className="w-3.5 h-3.5" />
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="chart" className="mt-6">
            <div className="space-y-4">
              {/* Symbol & Timeframe Controls */}
              <div className="flex items-center gap-4 bg-card/50 backdrop-blur-sm rounded-xl p-4 border border-border/50">
                <div className="flex items-center gap-2">
                  <span className="text-xl font-black text-primary tracking-tighter">{symbol}</span>
                  {chartData.length > 0 && (
                    <span className={cn(
                      "text-sm font-black tracking-tight",
                      chartData[chartData.length - 1]?.close >= chartData[0]?.close ? "text-emerald-500" : "text-red-500"
                    )}>
                      {chartData[chartData.length - 1]?.close?.toLocaleString()}
                    </span>
                  )}
                </div>
                <div className="ml-auto flex gap-1 bg-muted p-1 rounded-lg border border-border/50">
                  {["15m", "1h", "1d"].map((tf) => (
                    <button
                      key={tf}
                      onClick={() => setTimeframe(tf)}
                      className={cn(
                        "px-3 py-1 rounded-md text-[10px] font-black uppercase tracking-widest transition-all cursor-pointer",
                        timeframe === tf ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price Chart */}
              <div className="bg-card/50 backdrop-blur-sm rounded-xl p-6 border border-border/50" style={{ height: 400 }}>
                {chartLoading ? (
                  <div className="flex items-center justify-center h-full">
                    <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-8 h-8 text-primary" />
                  </div>
                ) : error ? (
                  <div className="flex items-center justify-center h-full text-red-500 font-black text-xs uppercase">
                    {error}
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={340}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsla(var(--border), 0.1)" />
                      <XAxis
                        dataKey="time"
                        tick={{ fontSize: 9, fill: "hsla(var(--muted-foreground), 0.6)", fontWeight: "bold" }}
                        tickFormatter={(v) => {
                          try { return new Date(v).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }); }
                          catch { return v; }
                        }}
                      />
                      <YAxis
                        domain={["auto", "auto"]}
                        tick={{ fontSize: 9, fill: "hsla(var(--muted-foreground), 0.6)", fontWeight: "bold" }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "hsla(var(--card), 0.95)",
                          border: "1px solid hsla(var(--border), 0.5)",
                          borderRadius: "12px",
                          fontSize: "10px",
                          fontWeight: "bold",
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="close"
                        stroke="var(--primary)"
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
                <div className="bg-card/50 backdrop-blur-sm rounded-xl p-4 border border-border/50" style={{ height: 200 }}>
                  <p className="text-[10px] text-muted-foreground mb-3 font-black uppercase tracking-widest">Market Volume</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <BarChart data={chartData.slice(-60)}>
                      <Bar dataKey="volume" fill="var(--chart-3)" opacity={0.6} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="bg-card/50 backdrop-blur-sm rounded-xl p-4 border border-border/50" style={{ height: 200 }}>
                  <p className="text-[10px] text-muted-foreground mb-3 font-black uppercase tracking-widest">RSI Momentum (14)</p>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={chartData.slice(-60)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsla(var(--border), 0.1)" />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 8, fill: "hsla(var(--muted-foreground), 0.4)" }} />
                      <Line type="monotone" dataKey="rsi" stroke="var(--chart-4)" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="crypto" className="mt-6">
            <div className="space-y-6">
              {loading ? (
                <div className="flex items-center justify-center py-40">
                  <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-12 h-12 text-primary opacity-30" />
                </div>
              ) : cryptoData ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Fear & Greed */}
                    <Card className="bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 transition-colors">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-[10px] font-black text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                          <FontAwesomeIcon icon={faHeartbeat as IconProp} className="w-3 h-3 text-purple-400" /> Sentiment Crypto
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="text-center pt-2">
                        <div className="relative w-36 h-36 mx-auto mb-4 group">
                          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                            <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                            <circle
                              cx="50" cy="50" r="42" fill="none"
                              stroke={cryptoData.fear_greed > 60 ? "#10b981" : cryptoData.fear_greed < 40 ? "#ef4444" : "#f59e0b"}
                              strokeWidth="8"
                              strokeDasharray={`${(cryptoData.fear_greed / 100) * 264} 264`}
                              strokeLinecap="round"
                              className="transition-all duration-1000 ease-out"
                            />
                          </svg>
                          <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-4xl font-extrabold tracking-tighter">{cryptoData.fear_greed}</span>
                            <span className="text-[8px] font-mono opacity-50">SCORE</span>
                          </div>
                        </div>
                        <Badge variant="secondary" className="px-4 py-1 text-xs font-bold bg-white/5 border-white/10 uppercase font-mono">
                          {cryptoData.fear_greed > 70 ? "Extreme Greed 🤑" 
                           : cryptoData.fear_greed > 55 ? "Greed" 
                           : cryptoData.fear_greed > 45 ? "Neutral"
                           : cryptoData.fear_greed > 30 ? "Fear" : "Extreme Fear 😱"}
                        </Badge>
                      </CardContent>
                    </Card>

                    {/* Net Flow */}
                    <Card className="bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 transition-colors flex flex-col justify-between">
                      <CardHeader className="pb-0">
                        <CardTitle className="text-[10px] font-black text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                          <FontAwesomeIcon icon={faLayerGroup as IconProp} className="w-3 h-3 text-emerald-400" /> Whale Net Flow
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="flex-1 flex flex-col justify-center py-6">
                        <p className="text-5xl font-black text-emerald-400 tracking-tighter mb-1 drop-shadow-sm">{cryptoData.net_flow}</p>
                        <p className="text-xs font-mono font-bold text-muted-foreground flex items-center gap-2 uppercase">
                          {cryptoData.symbol} Market Sentiment
                        </p>
                      </CardContent>
                      <div className="p-4 bg-muted/50 border-t border-border/50 flex items-center gap-3">
                        <Badge className={cn(
                          "px-4 py-1.5 text-[10px] font-black tracking-widest uppercase",
                          cryptoData.action === "BUY" ? "bg-emerald-500/20 text-emerald-500 border-emerald-500/20" : "bg-red-500/20 text-red-500 border-red-500/20"
                        )}>
                          <FontAwesomeIcon icon={(cryptoData.action === "BUY" ? faCircleArrowUp : faCircleArrowDown) as IconProp} className="w-3 h-3 mr-2" />
                          {cryptoData.action} SIGNAL
                        </Badge>
                      </div>
                    </Card>

                    {/* Score */}
                    <Card className="bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 transition-colors">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-[10px] font-black text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                          <FontAwesomeIcon icon={faBolt as IconProp} className="w-3 h-3 text-amber-400" /> Whale Power Score
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="h-full flex flex-col items-center justify-center gap-4 py-8">
                        <div className="text-7xl font-black bg-gradient-to-tr from-white to-white/40 bg-clip-text text-transparent tracking-tighter italic">
                          {cryptoData.score}
                        </div>
                        <div className="flex flex-col items-center gap-1">
                          <Badge variant="outline" className="text-[10px] border-white/10 font-mono text-muted-foreground">
                            EXCHANGE: {cryptoData.exchange || "GLOBAL"}
                          </Badge>
                          <p className="text-[9px] text-muted-foreground/40 font-mono uppercase">Calculated in real-time</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  <PaginatedAssetTable />
                </>
              ) : (
                <Card className="border-dashed border-white/10 bg-white/5">
                  <CardContent className="py-20 text-center flex flex-col items-center gap-4">
                    <FontAwesomeIcon icon={faCircleInfo as IconProp} className="w-10 h-10 text-muted-foreground opacity-20" />
                    <p className="text-sm text-muted-foreground font-mono italic">Market stream disconnected. Reconnecting...</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="forex" className="mt-6">
            <div className="space-y-6">
              {loading ? (
                <div className="flex items-center justify-center py-40">
                  <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-12 h-12 text-primary opacity-30" />
                </div>
              ) : forexData ? (
                <Card className="bg-card/50 backdrop-blur-sm border-border/50 shadow-2xl overflow-hidden">
                  <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 pb-5 bg-accent/20">
                    <div className="space-y-1">
                      <CardTitle className="text-2xl font-black tracking-tighter flex items-center gap-3">
                        <FontAwesomeIcon icon={faEarthAmericas as IconProp} className="w-5 h-5 text-primary" /> {forexData.pair}
                      </CardTitle>
                      <p className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em]">{forexData.session} SESSION ACTIVE</p>
                    </div>
                    <Badge className={`px-5 py-1.5 text-xs font-black tracking-widest shadow-lg ${
                      forexData.signal === "BUY" ? "bg-emerald-500 text-white"
                      : forexData.signal === "SELL" ? "bg-red-500 text-white"
                      : "bg-white/10 text-muted-foreground"
                    }`}>
                      {forexData.signal} SIGNAL
                    </Badge>
                  </CardHeader>

                  <CardContent className="pt-8">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-[0.3em] font-mono">Currency Strength Matrix</h3>
                      <div className="h-0.5 flex-1 mx-4 bg-white/5 rounded-full" />
                      <FontAwesomeIcon icon={faHeartbeat as IconProp} className="w-3 h-3 text-primary opacity-50" />
                    </div>
                    <div className="grid grid-cols-1 gap-5">
                      {Object.entries(forexData.strength || {}).sort((a, b) => (b[1] as number) - (a[1] as number)).map(([currency, value]) => (
                        <div key={currency} className="group flex items-center gap-6">
                          <div className="text-sm font-black w-10 font-mono tracking-tighter group-hover:text-primary transition-colors">{currency}</div>
                          <div className="flex-1 h-3.5 rounded-full bg-white/5 p-0.5 border border-white/5 overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(0,0,0,0.5)]"
                              style={{
                                width: `${Math.max(5, Math.min(100, ((value as number) + 100) / 2))}%`,
                                background: (value as number) > 0
                                  ? "linear-gradient(90deg, #10b981, #34d399)"
                                  : "linear-gradient(90deg, #ef4444, #f87171)",
                              }}
                            />
                          </div>
                          <div className={`text-xs font-black w-16 text-right font-mono transition-all ${(value as number) > 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {(value as number) > 0 ? "+" : ""}{(value as number).toFixed(1)}%
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-8">
                      <PaginatedAssetTable />
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-dashed border-white/10 bg-white/5 py-20">
                  <CardContent className="text-center italic text-muted-foreground font-mono opacity-50 text-sm">
                    Menghubungkan ke liquidity provider forex...
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="bandar" className="mt-6">
            <div className="space-y-6">
              {loading ? (
                <div className="flex items-center justify-center py-40">
                  <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-12 h-12 text-primary opacity-30" />
                </div>
              ) : bandarData ? (
                <Card className="bg-card/50 backdrop-blur-sm border-border/50 overflow-hidden shadow-2xl">
                  <CardHeader className="flex flex-row items-center justify-between border-b border-border/50 pb-5 bg-accent/20">
                    <div className="space-y-1">
                      <CardTitle className="text-3xl font-black tracking-tighter">
                        {bandarData.symbol} <span className="text-primary text-[10px] font-black px-2 py-0.5 rounded bg-primary/10 tracking-widest uppercase ml-2">Bandarmology</span>
                      </CardTitle>
                      <p className="text-[9px] text-muted-foreground tracking-[0.4em] font-black leading-none uppercase">Real-Time Flow Analysis</p>
                    </div>
                    <Badge className={`px-5 py-2 text-[10px] font-black tracking-[0.2em] shadow-[0_0_15px_rgba(0,0,0,0.4)] ${
                      bandarData.status.includes("ACCUM") ? "bg-emerald-500 text-white"
                      : bandarData.status.includes("DISTRIB") ? "bg-red-500 text-white"
                      : "bg-white/10 text-muted-foreground"
                    }`}>
                      {bandarData.status}
                    </Badge>
                  </CardHeader>

                  <CardContent className="pt-8 space-y-8">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                      <Card className="bg-accent/30 border-none shadow-inner group hover:bg-accent/50 transition-all cursor-default relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-16 h-16 bg-primary/10 rounded-bl-full -mr-8 -mt-8 group-hover:scale-150 transition-transform" />
                        <CardContent className="flex flex-col items-center justify-center py-6 gap-2">
                          <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">BANDAR SCORE</span>
                          <span className={cn(
                            "text-5xl font-black tracking-tighter",
                            bandarData.score > 0 ? "text-emerald-500" : "text-red-500"
                          )}>
                            {bandarData.score > 0 ? "+" : ""}{bandarData.score}
                          </span>
                        </CardContent>
                      </Card>

                      <Card className="bg-white/5 border-none shadow-inner group hover:bg-white/10 transition-all cursor-default relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-16 h-16 bg-primary/5 rounded-bl-full -mr-8 -mt-8 group-hover:scale-150 transition-transform" />
                        <CardContent className="flex flex-col items-center justify-center py-6 gap-2">
                          <span className="text-[10px] font-black text-muted-foreground uppercase tracking-wider font-mono">VOL RATIO</span>
                          <span className="text-5xl font-black tracking-tighter text-white">
                            {bandarData.vol_ratio?.toFixed(2)}<span className="text-xs text-muted-foreground ml-1">x</span>
                          </span>
                        </CardContent>
                      </Card>

                      <Card className="bg-accent/30 border-none shadow-inner group hover:bg-accent/50 transition-all cursor-default relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-16 h-16 bg-primary/10 rounded-bl-full -mr-8 -mt-8 group-hover:scale-150 transition-transform" />
                        <CardContent className="flex flex-col items-center justify-center py-6 gap-2">
                          <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">FLOW STATUS</span>
                          <span className="text-lg font-black tracking-widest text-primary uppercase text-center px-2 italic">
                            {bandarData.status}
                          </span>
                        </CardContent>
                      </Card>
                    </div>

                    <div className="bg-primary/5 border border-primary/20 rounded-xl p-5 flex items-start gap-5">
                      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <FontAwesomeIcon icon={faArrowTrendUp as IconProp} className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <h4 className="text-sm font-black text-primary uppercase tracking-widest mb-1">Expert Market Sentiment</h4>
                        <p className="text-xs text-muted-foreground/80 leading-relaxed font-black italic tracking-tight">&quot;{bandarData.message}&quot;</p>
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t border-white/5">
                      <PaginatedAssetTable />
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-dashed border-white/10 bg-white/5 py-24 text-center">
                  <CardContent className="flex flex-col items-center gap-4">
                    <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-10 h-10 text-primary opacity-20" />
                    <p className="text-sm text-white/40 font-mono tracking-tighter">Menganalisis pergerakan bandar untuk {symbol}...</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
    </div>
  );
}
