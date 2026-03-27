"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { alertsService } from "@/services/api";
import type { Alert } from "@/types";
import {
  Bell,
  Plus,
  Trash2,
  Loader2,
  X,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

export default function AlertsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Form state
  const [formSymbol, setFormSymbol] = useState("");
  const [formType, setFormType] = useState("PRICE");
  const [formCondition, setFormCondition] = useState("ABOVE");
  const [formTargetPrice, setFormTargetPrice] = useState("");
  const [formNote, setFormNote] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await alertsService.list();
      setAlerts(data);
    } catch {
      setError("Gagal memuat alerts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) fetchAlerts();
  }, [isAuthenticated, fetchAlerts]);

  const handleCreate = async () => {
    if (!formSymbol) return;
    setCreating(true);
    try {
      await alertsService.create({
        symbol: formSymbol.toUpperCase(),
        type: formType,
        condition: formType === "PRICE" ? formCondition : formCondition,
        target_price: formType === "PRICE" ? Number(formTargetPrice) : 0,
        note: formNote,
      });
      setShowModal(false);
      setFormSymbol("");
      setFormCondition("ABOVE");
      setFormTargetPrice("");
      setFormNote("");
      await fetchAlerts();
    } catch {
      setError("Gagal membuat alert");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await alertsService.delete(id);
      setAlerts((prev) => prev.filter((a) => (a.id || a._id) !== id));
    } catch {
      setError("Gagal menghapus alert");
    } finally {
      setDeleting(null);
    }
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
              Alerts
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              🔔 Notifikasi harga & formula — <span className="text-chart-5">アラート</span>
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/20 text-primary text-sm font-medium hover:bg-primary/30 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Buat Alert
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 px-4 py-3 mb-4 rounded-lg bg-trade-down/10 border border-trade-down/20 text-trade-down text-sm">
            <AlertTriangle className="w-4 h-4" /> {error}
          </div>
        )}

        {/* Alerts List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="glass-panel rounded-xl p-12 text-center">
            <Bell className="w-12 h-12 mx-auto text-muted-foreground mb-3 opacity-40" />
            <p className="text-muted-foreground">Belum ada alert.</p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-4 text-primary text-sm hover:underline cursor-pointer"
            >
              + Buat alert pertamamu
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((a) => {
              const id = a.id || a._id || "";
              return (
                <div
                  key={id}
                  className="glass-panel rounded-xl p-4 flex items-center gap-4 hover:border-primary/20 transition-all"
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                    a.status === "ACTIVE" ? "bg-trade-up/15" : "bg-white/10"
                  }`}>
                    {a.status === "ACTIVE" ? (
                      <Bell className="w-5 h-5 text-trade-up" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold">{a.symbol}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-muted-foreground">
                        {a.type}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        a.status === "ACTIVE" ? "bg-trade-up/15 text-trade-up" : "bg-white/10 text-muted-foreground"
                      }`}>
                        {a.status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 truncate">
                      {a.type === "PRICE"
                        ? `${a.condition} ${a.target_price.toLocaleString()}`
                        : a.condition}
                      {a.note && ` — ${a.note}`}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(id)}
                    disabled={deleting === id}
                    className="p-2 rounded-lg hover:bg-trade-down/10 text-muted-foreground hover:text-trade-down transition-all cursor-pointer disabled:opacity-50"
                  >
                    {deleting === id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Create Alert Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="glass-panel rounded-2xl p-6 w-full max-w-md border border-white/10 shadow-2xl">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-bold">Buat Alert Baru</h2>
                <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground cursor-pointer">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Symbol */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Symbol</label>
                  <input
                    type="text"
                    value={formSymbol}
                    onChange={(e) => setFormSymbol(e.target.value)}
                    placeholder="BBCA.JK"
                    className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
                  />
                </div>

                {/* Type */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Tipe Alert</label>
                  <div className="flex gap-2">
                    {["PRICE", "FORMULA"].map((t) => (
                      <button
                        key={t}
                        onClick={() => setFormType(t)}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                          formType === t
                            ? "bg-primary/20 text-primary border border-primary/30"
                            : "bg-white/5 text-muted-foreground border border-white/10"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Condition */}
                {formType === "PRICE" ? (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Kondisi</label>
                      <select
                        value={formCondition}
                        onChange={(e) => setFormCondition(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm outline-none"
                      >
                        <option value="ABOVE">Di Atas (Above)</option>
                        <option value="BELOW">Di Bawah (Below)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Target Harga</label>
                      <input
                        type="number"
                        value={formTargetPrice}
                        onChange={(e) => setFormTargetPrice(e.target.value)}
                        placeholder="10000"
                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
                      />
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block">Formula</label>
                    <input
                      type="text"
                      value={formCondition}
                      onChange={(e) => setFormCondition(e.target.value)}
                      placeholder="RSI < 30 AND VOLUME > 1000000"
                      className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
                    />
                  </div>
                )}

                {/* Note */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Catatan (opsional)</label>
                  <input
                    type="text"
                    value={formNote}
                    onChange={(e) => setFormNote(e.target.value)}
                    placeholder="Beli jika tembus resistance"
                    className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm outline-none focus:border-primary/40"
                  />
                </div>

                <button
                  onClick={handleCreate}
                  disabled={!formSymbol || creating}
                  className="w-full py-2.5 rounded-lg bg-primary/20 text-primary font-medium hover:bg-primary/30 transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  Buat Alert
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
