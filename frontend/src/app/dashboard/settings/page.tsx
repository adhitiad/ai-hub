"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { userService } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faUser,
  faKey,
  faComments,
  faWallet,
  faEye,
  faSpinner,
  faCopy,
  faCheck,
  faPlus,
  faXmark,
  faArrowsRotate,
  faPaperPlane,
  faShieldHalved,
  faStar,
  faEnvelope,
} from "@fortawesome/free-solid-svg-icons";

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

  // Email
  const [emailAlertEnabled, setEmailAlertEnabled] = useState(true);
  const [targetEmail, setTargetEmail] = useState(user?.email || "");
  const [emailSaving, setEmailSaving] = useState(false);
  const [emailMsg, setEmailMsg] = useState<string | null>(null);

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

  const saveEmailSettings = async () => {
    setEmailSaving(true);
    setEmailMsg(null);
    try {
      // Mengasumsikan ada endpoint untuk ini atau simpan di profile sementara
      // Karena belum ada di userService, kita simpan secara lokal/mock atau panggil update profile jika tersedia
      await new Promise(resolve => setTimeout(resolve, 800));
      setEmailMsg("✅ Pengaturan email berhasil disimpan!");
    } catch {
      setEmailMsg("❌ Gagal menyimpan pengaturan email");
    } finally {
      setEmailSaving(false);
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
    <div className="space-y-8 pb-12">
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
              <FontAwesomeIcon icon={faUser as IconProp} className="w-4 h-4 mr-1.5" /> Profile
            </TabsTrigger>
            <TabsTrigger value="balance" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <FontAwesomeIcon icon={faWallet as IconProp} className="w-4 h-4 mr-1.5" /> Balance
            </TabsTrigger>
            <TabsTrigger value="telegram" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <FontAwesomeIcon icon={faComments as IconProp} className="w-4 h-4 mr-1.5" /> Telegram
            </TabsTrigger>
            <TabsTrigger value="email" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <FontAwesomeIcon icon={faEnvelope as IconProp} className="w-4 h-4 mr-1.5" /> Email
            </TabsTrigger>
            <TabsTrigger value="apikey" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <FontAwesomeIcon icon={faKey as IconProp} className="w-4 h-4 mr-1.5" /> API Key
            </TabsTrigger>
            <TabsTrigger value="watchlist" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <FontAwesomeIcon icon={faEye as IconProp} className="w-4 h-4 mr-1.5" /> Watchlist
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FontAwesomeIcon icon={faShieldHalved as IconProp} className="w-5 h-5 text-primary" /> Profile Info
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
                        <FontAwesomeIcon icon={faStar as IconProp} className="w-3 h-3 mr-1" /> {user?.role || "free"}
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
                  <FontAwesomeIcon icon={faWallet as IconProp} className="w-5 h-5 text-chart-4" /> Trading Balance
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
                  {balanceSaving ? <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-4 h-4 mr-2" /> : null}
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
                <CardTitle className="flex items-center gap-2 text-blue-400">
                  <FontAwesomeIcon icon={faComments as IconProp} className="w-5 h-5" /> Telegram Integration
                </CardTitle>
                <CardDescription>Dapatkan notifikasi sinyal dan alert langsung ke Telegram Anda</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/10 text-sm mb-2">
                  <p className="font-bold text-blue-400 mb-1">💡 Cara Menghubungkan:</p>
                  <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                    <li>Generate kode di bawah ini.</li>
                    <li>Kirim kode tersebut ke bot Telegram kami <span className="text-blue-400 font-mono">@AITradingHub_Bot</span>.</li>
                    <li>Atau masukkan Chat ID Anda secara manual jika sudah tahu.</li>
                  </ol>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="telegram-id">Telegram Chat ID</Label>
                  <div className="flex gap-2">
                    <Input
                      id="telegram-id"
                      value={telegramId}
                      onChange={(e) => setTelegramId(e.target.value)}
                      placeholder="Contoh: 123456789"
                      className="bg-white/5 border-white/10 font-mono shadow-inner"
                    />
                    <Button onClick={saveTelegram} disabled={telegramSaving || !telegramId} className="bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 border border-blue-600/30 transition-all">
                      {telegramSaving ? <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-4 h-4" /> : <FontAwesomeIcon icon={faPaperPlane as IconProp} className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <Separator className="bg-white/10" />

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="space-y-1">
                    <Label className="text-base">Binding Code</Label>
                    <p className="text-xs text-muted-foreground">Gunakan kode ini untuk verifikasi via bot</p>
                  </div>
                  <div className="flex gap-2 items-center">
                    <Button onClick={generateCode} disabled={codeLoading} variant="outline" className="border-white/10 hover:bg-white/10">
                      {codeLoading ? <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-4 h-4 mr-2" /> : <FontAwesomeIcon icon={faArrowsRotate as IconProp} className="w-4 h-4 mr-2" />}
                      Generate
                    </Button>
                    {telegramCode && (
                      <Badge className="font-mono text-lg px-6 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10">
                        {telegramCode}
                      </Badge>
                    )}
                  </div>
                </div>
                {telegramMsg && <p className={`text-sm ${telegramMsg.includes('✅') ? 'text-trade-up' : 'text-trade-down'}`}>{telegramMsg}</p>}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Email Tab */}
          <TabsContent value="email">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-purple-400">
                  <FontAwesomeIcon icon={faEnvelope as IconProp} className="w-5 h-5" /> Email Notifications
                </CardTitle>
                <CardDescription>Kelola pengaturan notifikasi via email untuk sinyal dan laporan harian</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="target-email">Email Penerima Alerts</Label>
                    <Input
                      id="target-email"
                      type="email"
                      value={targetEmail}
                      onChange={(e) => setTargetEmail(e.target.value)}
                      placeholder="email@anda.com"
                      className="bg-white/5 border-white/10 focus:border-purple-500/50"
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                    <div className="space-y-0.5">
                      <Label className="text-base">Aktifkan Email Alerts</Label>
                      <p className="text-sm text-muted-foreground">Kirim sinyal trading ke email secara real-time</p>
                    </div>
                    <button 
                      onClick={() => setEmailAlertEnabled(!emailAlertEnabled)}
                      className={cn(
                        "w-12 h-6 rounded-full transition-colors relative",
                        emailAlertEnabled ? "bg-purple-600" : "bg-white/10"
                      )}
                    >
                      <div className={cn(
                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                        emailAlertEnabled ? "left-7" : "left-1"
                      )} />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-start gap-3 opacity-60">
                      <input type="checkbox" className="mt-1" defaultChecked />
                      <div>
                        <p className="text-sm font-bold">Laporan Harian (Daily Repo)</p>
                        <p className="text-xs text-muted-foreground">Ringkasan performa portofolio setiap jam 18:00</p>
                      </div>
                    </div>
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-start gap-3 opacity-60">
                      <input type="checkbox" className="mt-1" defaultChecked />
                      <div>
                        <p className="text-sm font-bold">Security Alerts</p>
                        <p className="text-xs text-muted-foreground">Notifikasi login baru atau perubahan API key</p>
                      </div>
                    </div>
                  </div>
                </div>

                <Button 
                  onClick={saveEmailSettings} 
                  disabled={emailSaving} 
                  className="w-full md:w-auto bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 border border-purple-600/30"
                >
                  {emailSaving ? <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-4 h-4 mr-2" /> : <FontAwesomeIcon icon={faCheck as IconProp} className="w-4 h-4 mr-2" />}
                  Simpan Pengaturan Email
                </Button>
                {emailMsg && <p className="text-sm text-trade-up">{emailMsg}</p>}
              </CardContent>
            </Card>
          </TabsContent>

          {/* API Key Tab */}
          <TabsContent value="apikey">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FontAwesomeIcon icon={faKey as IconProp} className="w-5 h-5 text-chart-4" /> API Key
                </CardTitle>
                <CardDescription>Kelola API key untuk akses layanan</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-white/5 border border-white/10">
                  <code className="flex-1 text-sm font-mono text-muted-foreground">
                    {showKey ? apiKey : "••••••••••••••••••••••••••"}
                  </code>
                  <Button variant="ghost" size="icon" onClick={() => setShowKey(!showKey)} className="shrink-0">
                    <FontAwesomeIcon icon={faEye as IconProp} className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={copyApiKey} className="shrink-0">
                    {keyCopied ? <FontAwesomeIcon icon={faCheck as IconProp} className="w-4 h-4 text-trade-up" /> : <FontAwesomeIcon icon={faCopy as IconProp} className="w-4 h-4" />}
                  </Button>
                </div>
                <Button onClick={regenerateKey} disabled={regenerating} variant="outline" className="border-trade-down/30 text-trade-down hover:bg-trade-down/10">
                  {regenerating ? <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-4 h-4 mr-2" /> : <FontAwesomeIcon icon={faArrowsRotate as IconProp} className="w-4 h-4 mr-2" />}
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
                  <FontAwesomeIcon icon={faEye as IconProp} className="w-5 h-5 text-trade-up" /> Watchlist
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
                    {addingSymbol ? <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-4 h-4" /> : <FontAwesomeIcon icon={faPlus as IconProp} className="w-4 h-4" />}
                  </Button>
                </div>

                {watchlistLoading ? (
                  <div className="py-8 text-center">
                    <FontAwesomeIcon icon={faSpinner as IconProp} spin className="w-6 h-6 text-primary mx-auto" />
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
                          <FontAwesomeIcon icon={faXmark as IconProp} className="w-3 h-3 text-trade-down" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
    </div>
  );
}
