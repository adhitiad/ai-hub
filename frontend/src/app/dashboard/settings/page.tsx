"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { userService } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  Settings,
  User,
  Key,
  MessageSquare,
  Wallet,
  Eye,
  Loader2,
  Copy,
  Check,
  Plus,
  X,
  RefreshCw,
  Send,
  Shield,
  Sparkles,
} from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const { isAuthenticated, user, apiKey } = useAuthStore();

  // Balance
  const [stockBalance, setStockBalance] = useState("100000000");
  const [forexBalance, setForexBalance] = useState("10000");
  const [balanceSaving, setBalanceSaving] = useState(false);
  const [balanceMsg, setBalanceMsg] = useState<string | null>(null);

  // Telegram
  const [telegramId, setTelegramId] = useState("");
  const [telegramSaving, setTelegramSaving] = useState(false);
  const [telegramMsg, setTelegramMsg] = useState<string | null>(null);
  const [telegramCode, setTelegramCode] = useState<string | null>(null);
  const [codeLoading, setCodeLoading] = useState(false);

  // API Key
  const [showKey, setShowKey] = useState(false);
  const [keyCopied, setKeyCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [regenMsg, setRegenMsg] = useState<string | null>(null);

  // Watchlist
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [newSymbol, setNewSymbol] = useState("");
  const [addingSymbol, setAddingSymbol] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const fetchWatchlist = useCallback(async () => {
    setWatchlistLoading(true);
    try {
      const { data } = await userService.getWatchlist();
      setWatchlist(data);
    } catch {
      // silent
    } finally {
      setWatchlistLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) fetchWatchlist();
  }, [isAuthenticated, fetchWatchlist]);

  const saveBalance = async () => {
    setBalanceSaving(true);
    setBalanceMsg(null);
    try {
      await userService.updateBalance(Number(stockBalance), Number(forexBalance));
      setBalanceMsg("✅ Saldo berhasil disimpan!");
    } catch {
      setBalanceMsg("❌ Gagal menyimpan saldo");
    } finally {
      setBalanceSaving(false);
    }
  };

  const saveTelegram = async () => {
    setTelegramSaving(true);
    setTelegramMsg(null);
    try {
      await userService.connectTelegram(telegramId);
      setTelegramMsg("✅ Telegram terhubung!");
    } catch {
      setTelegramMsg("❌ Gagal menghubungkan Telegram");
    } finally {
      setTelegramSaving(false);
    }
  };

  const generateCode = async () => {
    setCodeLoading(true);
    try {
      const { data } = await userService.generateTelegramCode();
      setTelegramCode((data as { code?: string }).code || JSON.stringify(data));
    } catch {
      setTelegramCode("Gagal generate kode");
    } finally {
      setCodeLoading(false);
    }
  };

  const copyApiKey = () => {
    if (apiKey) navigator.clipboard.writeText(apiKey);
    setKeyCopied(true);
    setTimeout(() => setKeyCopied(false), 2000);
  };

  const regenerateKey = async () => {
    setRegenerating(true);
    setRegenMsg(null);
    try {
      await userService.regenerateApiKey();
      setRegenMsg("✅ API key di-regenerate. Silakan login ulang.");
    } catch {
      setRegenMsg("❌ Gagal regenerate API key");
    } finally {
      setRegenerating(false);
    }
  };

  const addWatchlist = async () => {
    if (!newSymbol.trim()) return;
    setAddingSymbol(true);
    try {
      await userService.addWatchlist(newSymbol.toUpperCase());
      setWatchlist((prev) => [...prev, newSymbol.toUpperCase()]);
      setNewSymbol("");
    } catch {
      // silent
    } finally {
      setAddingSymbol(false);
    }
  };

  const removeWatchlist = async (sym: string) => {
    try {
      await userService.removeWatchlist(sym);
      setWatchlist((prev) => prev.filter((s) => s !== sym));
    } catch {
      // silent
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
            Settings
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            ⚙️ Kelola akun & preferensi — <span className="text-chart-5">設定</span>
          </p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="glass-panel border border-white/10 p-1">
            <TabsTrigger value="profile" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <User className="w-4 h-4 mr-1.5" /> Profile
            </TabsTrigger>
            <TabsTrigger value="balance" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <Wallet className="w-4 h-4 mr-1.5" /> Balance
            </TabsTrigger>
            <TabsTrigger value="telegram" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <MessageSquare className="w-4 h-4 mr-1.5" /> Telegram
            </TabsTrigger>
            <TabsTrigger value="apikey" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <Key className="w-4 h-4 mr-1.5" /> API Key
            </TabsTrigger>
            <TabsTrigger value="watchlist" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <Eye className="w-4 h-4 mr-1.5" /> Watchlist
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-primary" /> Profile Info
                </CardTitle>
                <CardDescription>Informasi akun anda</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
                    <span className="text-2xl font-bold text-white">
                      {user?.email?.[0]?.toUpperCase() || "U"}
                    </span>
                  </div>
                  <div>
                    <p className="text-lg font-bold">{user?.email}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="border-primary/30 text-primary capitalize">
                        <Sparkles className="w-3 h-3 mr-1" /> {user?.role || "free"}
                      </Badge>
                      <Badge variant="outline" className="border-trade-up/30 text-trade-up">
                        Active
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Balance Tab */}
          <TabsContent value="balance">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wallet className="w-5 h-5 text-chart-4" /> Trading Balance
                </CardTitle>
                <CardDescription>Atur saldo virtual untuk simulasi trading</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="stock-balance">Saham (IDR)</Label>
                    <Input
                      id="stock-balance"
                      type="number"
                      value={stockBalance}
                      onChange={(e) => setStockBalance(e.target.value)}
                      className="bg-white/5 border-white/10 font-mono"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="forex-balance">Forex (USD)</Label>
                    <Input
                      id="forex-balance"
                      type="number"
                      value={forexBalance}
                      onChange={(e) => setForexBalance(e.target.value)}
                      className="bg-white/5 border-white/10 font-mono"
                    />
                  </div>
                </div>
                <Button onClick={saveBalance} disabled={balanceSaving} className="bg-primary/20 text-primary hover:bg-primary/30">
                  {balanceSaving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Simpan Balance
                </Button>
                {balanceMsg && <p className="text-sm">{balanceMsg}</p>}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Telegram Tab */}
          <TabsContent value="telegram">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" /> Telegram Integration
                </CardTitle>
                <CardDescription>Hubungkan akun Telegram untuk notifikasi sinyal</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="telegram-id">Telegram Chat ID</Label>
                  <div className="flex gap-2">
                    <Input
                      id="telegram-id"
                      value={telegramId}
                      onChange={(e) => setTelegramId(e.target.value)}
                      placeholder="123456789"
                      className="bg-white/5 border-white/10 font-mono"
                    />
                    <Button onClick={saveTelegram} disabled={telegramSaving || !telegramId} className="bg-blue-600/20 text-blue-400 hover:bg-blue-600/30">
                      {telegramSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <Separator className="bg-white/10" />

                <div className="space-y-2">
                  <Label>Generate Binding Code</Label>
                  <div className="flex gap-2 items-center">
                    <Button onClick={generateCode} disabled={codeLoading} variant="outline" className="border-white/10">
                      {codeLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Key className="w-4 h-4 mr-2" />}
                      Generate Code
                    </Button>
                    {telegramCode && (
                      <Badge className="font-mono text-sm px-4 py-1.5 bg-chart-4/20 text-chart-4">
                        {telegramCode}
                      </Badge>
                    )}
                  </div>
                </div>
                {telegramMsg && <p className="text-sm">{telegramMsg}</p>}
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Key Tab */}
          <TabsContent value="apikey">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="w-5 h-5 text-chart-4" /> API Key
                </CardTitle>
                <CardDescription>Kelola API key untuk akses layanan</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-white/5 border border-white/10">
                  <code className="flex-1 text-sm font-mono text-muted-foreground">
                    {showKey ? apiKey : "••••••••••••••••••••••••••"}
                  </code>
                  <Button variant="ghost" size="icon" onClick={() => setShowKey(!showKey)} className="shrink-0">
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={copyApiKey} className="shrink-0">
                    {keyCopied ? <Check className="w-4 h-4 text-trade-up" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
                <Button onClick={regenerateKey} disabled={regenerating} variant="outline" className="border-trade-down/30 text-trade-down hover:bg-trade-down/10">
                  {regenerating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                  Regenerate API Key
                </Button>
                {regenMsg && <p className="text-sm">{regenMsg}</p>}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Watchlist Tab */}
          <TabsContent value="watchlist">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-trade-up" /> Watchlist
                </CardTitle>
                <CardDescription>Aset yang anda pantau</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    value={newSymbol}
                    onChange={(e) => setNewSymbol(e.target.value)}
                    placeholder="Tambah simbol (e.g. BBCA.JK)"
                    className="bg-white/5 border-white/10"
                    onKeyDown={(e) => e.key === "Enter" && addWatchlist()}
                  />
                  <Button onClick={addWatchlist} disabled={addingSymbol || !newSymbol.trim()} className="bg-trade-up/20 text-trade-up hover:bg-trade-up/30">
                    {addingSymbol ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  </Button>
                </div>

                {watchlistLoading ? (
                  <div className="py-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-primary mx-auto" />
                  </div>
                ) : watchlist.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">Watchlist kosong.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {watchlist.map((sym) => (
                      <Badge
                        key={sym}
                        variant="outline"
                        className="px-3 py-1.5 text-sm border-white/10 hover:border-trade-down/30 group flex items-center gap-1.5 cursor-default"
                      >
                        {sym}
                        <button
                          onClick={() => removeWatchlist(sym)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                        >
                          <X className="w-3 h-3 text-trade-down" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
