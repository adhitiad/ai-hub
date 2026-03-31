import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TradingSignal } from "@/types";
import { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faArrowTrendUp,
  faChartSimple,
  faClock,
  faRobot,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { formatDistanceToNow } from "date-fns";
import { id as idLocale } from "date-fns/locale";

const SignalCard = ({ signal }: { signal: TradingSignal }) => {
  const action = signal.action?.toLowerCase() || "";
  const isBuy = action.includes("buy");
  const isSell = action.includes("sell");

  const entryPrice =
    signal.fill_price ||
    signal.price ||
    signal.entry_price ||
    signal.price_at_signal ||
    0;
  const tpPrice = signal.tp || signal.take_profit || signal.target_price || 0;
  const slPrice = signal.sl || signal.stop_loss || signal.stop_price || 0;

  const createdDate = signal.created_at
    ? new Date(signal.created_at)
    : new Date();
  const timeAgo = formatDistanceToNow(createdDate, {
    addSuffix: true,
    locale: idLocale,
  });

  return (
    <Card
      className={cn(
        "group relative overflow-hidden border-border/50 bg-card/40 backdrop-blur-xl transition-all duration-500 hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/10 rounded-3xl",
        isBuy
          ? "hover:border-emerald-500/50"
          : isSell
            ? "hover:border-destructive/50"
            : "",
      )}
    >
      {/* Visual Accent Gradient */}
      <div
        className={cn(
          "absolute top-0 right-0 w-32 h-32 blur-[80px] opacity-10 -z-10 group-hover:opacity-30 transition-opacity duration-700",
          isBuy ? "bg-emerald-500" : isSell ? "bg-destructive" : "bg-primary",
        )}
      />

      <CardHeader className="pb-4 relative pt-6 px-6">
        <div className="flex justify-between items-start">
          <div className="space-y-1.5 font-mono">
            <div className="flex items-center gap-3">
              <h3 className="text-3xl font-black text-foreground group-hover:text-primary transition-colors tracking-tighter uppercase">
                {signal.symbol}
              </h3>
              {signal.status !== "OPEN" && (
                <Badge
                  className={cn(
                    "text-[10px] px-2 h-5 font-black uppercase tracking-widest border-0",
                    signal.status === "WIN"
                      ? "bg-emerald-500 text-black"
                      : "bg-destructive text-destructive-foreground",
                  )}
                >
                  {signal.status}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-black">
              <FontAwesomeIcon
                icon={faClock as IconProp}
                className="w-3 h-3 opacity-40"
              />
              <span className="uppercase tracking-widest">{timeAgo}</span>
            </div>
          </div>

            <div className="flex flex-col items-end gap-2">
              <div
                className={cn(
                  "px-5 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.2em] border shadow-lg transition-all",
                  isBuy
                    ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                    : isSell
                      ? "bg-destructive/10 text-destructive border-destructive/30"
                      : "bg-muted/5 text-muted-foreground border-border/50",
                )}
              >
                {signal.action}
              </div>
              <div className="flex gap-2">
                {signal.asset_type && (
                  <Badge variant="outline" className="text-[8px] h-4 px-1.5 font-bold uppercase tracking-widest border-border/50 text-muted-foreground bg-muted/20">
                    {signal.asset_type}
                  </Badge>
                )}
                {signal.rank && (
                  <Badge 
                    className={cn(
                      "text-[8px] h-4 px-1.5 font-black uppercase tracking-widest border-0",
                      signal.rank === "ELITE" ? "bg-chart-5 text-black animate-pulse" :
                      signal.rank === "PREMIUM" ? "bg-primary text-primary-foreground" :
                      "bg-muted text-muted-foreground"
                    )}
                  >
                    {signal.rank}
                  </Badge>
                )}
              </div>
              {signal.Prob && (
                <div className="text-[10px] font-black text-muted-foreground/40 tracking-[0.3em] uppercase">
                  CONF: <span className="text-foreground">{signal.Prob}</span>
                </div>
              )}
            </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 px-6 pb-6">
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-muted/30 border border-border/50 rounded-2xl p-4 flex flex-col items-center justify-center group-hover:bg-muted/50 transition-all duration-300">
            <span className="text-[9px] font-black uppercase text-muted-foreground/50 mb-1.5 tracking-widest">
              Entry
            </span>
            <span className="text-sm font-black text-foreground font-mono">
              {entryPrice?.toLocaleString() ?? "N/A"}
            </span>
          </div>
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-4 flex flex-col items-center justify-center group-hover:bg-emerald-500/20 transition-all duration-300">
            <span className="text-[9px] font-black uppercase text-emerald-500/60 mb-1.5 tracking-widest">
              Target
            </span>
            <span className="text-sm font-black text-emerald-500 font-mono">
              {tpPrice?.toLocaleString() ?? "N/A"}
            </span>
          </div>
          <div className="bg-destructive/10 border border-destructive/20 rounded-2xl p-4 flex flex-col items-center justify-center group-hover:bg-destructive/20 transition-all duration-300">
            <span className="text-[9px] font-black uppercase text-destructive/60 mb-1.5 tracking-widest">
              Stop{" "}
            </span>
            <span className="text-sm font-black text-destructive font-mono">
              {slPrice?.toLocaleString() ?? "N/A"}
            </span>
          </div>
        </div>

        {signal.AI_Analysis && (
          <div className="rounded-2xl bg-gradient-to-br from-muted/40 to-muted/10 border border-border/50 p-4 relative overflow-hidden group/analysis hover:border-primary/30 transition-all">
            <div className="absolute -top-2 -right-2 p-2 opacity-5 group-hover/analysis:opacity-20 transition-opacity">
              <FontAwesomeIcon
                icon={faChartSimple as IconProp}
                className="w-12 h-12 text-primary"
              />
            </div>
            <h4 className="text-[10px] font-black text-primary uppercase tracking-[0.3em] mb-2.5 flex items-center gap-2">
              <FontAwesomeIcon icon={faRobot as IconProp} className="w-3 h-3" />
              Neural Insight
            </h4>
            <p className="text-xs text-muted-foreground italic leading-relaxed font-bold group-hover:text-foreground/80 transition-colors">
              &quot;{signal.AI_Analysis}&quot;
            </p>
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <div className="flex gap-4">
            <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-muted-foreground/60 transition-colors hover:text-emerald-500">
              <FontAwesomeIcon
                icon={faArrowTrendUp as IconProp}
                className="w-3 h-3 text-emerald-500"
              />
              Trend: OK
            </div>
            <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-muted-foreground/60 transition-colors hover:text-blue-500">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full shadow-[0_0_5px_rgba(59,130,246,0.5)]" />
              V-Flow: Hi
            </div>
          </div>

          <div className="text-[9px] text-muted-foreground/30 font-black tracking-widest uppercase bg-muted/50 px-2 py-0.5 rounded">
            {signal.lot_size} LOT
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SignalCard;
