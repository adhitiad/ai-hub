/**
 * Hook `useSymbols` — Mengambil daftar simbol dari database backend.
 * Fallback otomatis ke konstanta lokal (`symbols.ts`) jika API gagal.
 *
 * Gunakan hook ini di semua komponen yang memerlukan dropdown simbol agar
 * daftar simbol selalu up-to-date dari database.
 */

import { useState, useEffect } from "react";
import { assetsService, type AssetFromDB } from "@/services/api";
import { SYMBOL_OPTIONS, type SymbolOption } from "@/lib/symbols";

export interface GroupedSymbols {
  group: string;
  options: SymbolOption[];
}

/** Konversi AssetFromDB ke SymbolOption dengan label & flag otomatis */
function toSymbolOption(asset: AssetFromDB): SymbolOption {
  const categoryMap: Record<string, SymbolOption["category"]> = {
    FOREX: "Forex",
    STOCKS_INDO: "Saham IDX",
    STOCKS_US: "Saham US",
    CRYPTO: "Crypto",
  };

  const flagMap: Record<string, string> = {
    FOREX: "💱",
    STOCKS_INDO: "🇮🇩",
    STOCKS_US: "🇺🇸",
    CRYPTO: "₿",
  };

  const cat = categoryMap[asset.category?.toUpperCase()] ?? "Saham IDX";
  const flag = flagMap[asset.category?.toUpperCase()] ?? "📊";

  return {
    value: asset.symbol,
    label: asset.label ?? `${asset.symbol} — ${asset.type}`,
    category: cat,
    flag,
  };
}

/** Kelompokkan array SymbolOption berdasarkan kategori */
function groupSymbols(options: SymbolOption[]): GroupedSymbols[] {
  const order = ["Saham IDX", "Saham US", "Crypto", "Forex"] as const;
  const labelMap: Record<string, string> = {
    "Saham IDX": "🇮🇩 Saham IDX",
    "Saham US": "🇺🇸 Saham US",
    Crypto: "₿ Crypto",
    Forex: "💱 Forex",
  };

  return order
    .map((cat) => ({
      group: labelMap[cat],
      options: options.filter((o) => o.category === cat),
    }))
    .filter((g) => g.options.length > 0);
}

interface UseSymbolsReturn {
  /** Semua simbol flat, siap untuk native <select> */
  symbols: SymbolOption[];
  /** Simbol yang sudah dikelompokkan, siap untuk <optgroup> */
  grouped: GroupedSymbols[];
  loading: boolean;
  /** Sumber data: "api" = dari database, "local" = fallback dari konstanta */
  source: "api" | "local";
}

export function useSymbols(): UseSymbolsReturn {
  const [symbols, setSymbols] = useState<SymbolOption[]>(SYMBOL_OPTIONS);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState<"api" | "local">("local");

  useEffect(() => {
    let cancelled = false;

    const fetchSymbols = async () => {
      try {
        const { data } = await assetsService.list();
        if (cancelled) return;

        if (data.assets && data.assets.length > 0) {
          const converted = data.assets.map(toSymbolOption);
          setSymbols(converted);
          setSource("api");
        } else {
          // DB kosong → pakai fallback lokal
          setSource("local");
        }
      } catch {
        // API gagal → pakai fallback lokal, tidak perlu show error
        if (!cancelled) setSource("local");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchSymbols();
    return () => {
      cancelled = true;
    };
  }, []);

  return {
    symbols,
    grouped: groupSymbols(symbols),
    loading,
    source,
  };
}
