"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { subscriptionService } from "@/services/api";
import { useAuthStore } from "@/stores/useAuthStore";
import type { SubscriptionPlan } from "@/types";
import { Check, CreditCard, Crown, Loader2, Star, Zap } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const PLAN_ICONS: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  free: Star,
  pro: Zap,
  premium: Crown,
};

const PLAN_GRADIENTS: Record<string, string> = {
  free: "from-slate-400 to-slate-600",
  pro: "from-emerald-400 to-cyan-500",
  premium: "from-purple-400 to-pink-500",
};

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [plans, setPlans] = useState<Record<string, SubscriptionPlan>>({});
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchPlans = async () => {
      setLoading(true);
      try {
        const { data } = await subscriptionService.getPlans();
        setPlans(data);
      } catch (err) {
        console.error("Failed to fetch plans:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  const planKeys = Object.keys(plans);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          Pilih Plan Anda
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          💎 Tingkatkan kemampuan trading AI —{" "}
          <span className="text-chart-5">プラン</span>
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : planKeys.length === 0 ? (
        <div className="text-center py-20">
          <CreditCard className="w-12 h-12 mx-auto text-muted-foreground opacity-30 mb-3" />
          <p className="text-muted-foreground">
            Belum ada data paket berlangganan.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {planKeys.map((key) => {
            const plan = plans[key];
            const name = key.toLowerCase();
            const Icon = PLAN_ICONS[name] || Star;
            const gradient =
              PLAN_GRADIENTS[name] || "from-slate-400 to-slate-600";
            const isCurrentPlan =
              user?.role === name || (user?.role === "free" && name === "free");
            const isPremium = name === "premium";

            return (
              <Card
                key={key}
                className={`glass-panel border-white/10 relative overflow-hidden transition-all hover:scale-[1.02] hover:shadow-lg ${
                  isPremium ? "border-purple-500/30 shadow-purple-500/10" : ""
                }`}
              >
                {isPremium && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500" />
                )}

                <CardHeader className="text-center pb-2">
                  <div
                    className={`w-14 h-14 rounded-2xl mx-auto mb-3 bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg`}
                  >
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <CardTitle className="text-lg capitalize">
                    {plan.name || key}
                  </CardTitle>
                  <CardDescription>
                    {plan.daily_requests_limit
                      ? `${plan.daily_requests_limit} requests/hari`
                      : "Unlimited"}
                  </CardDescription>
                </CardHeader>

                <CardContent className="text-center pb-4">
                  <div className="mb-4">
                    <span className="text-4xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
                      {plan.price === 0 ? "Gratis" : `$${plan.price}`}
                    </span>
                    {plan.price > 0 && (
                      <span className="text-sm text-muted-foreground">
                        /bulan
                      </span>
                    )}
                  </div>

                  <ul className="space-y-2 text-left">
                    {(plan.features || []).map((feature, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Check className="w-4 h-4 text-trade-up shrink-0 mt-0.5" />
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>

                <CardFooter>
                  {isCurrentPlan ? (
                    <Badge className="w-full justify-center py-2 bg-primary/20 text-primary">
                      Plan Aktif
                    </Badge>
                  ) : (
                    <Button
                      className={`w-full bg-gradient-to-r ${gradient} text-white hover:opacity-90`}
                      onClick={() => router.push("/dashboard/settings")}
                    >
                      Upgrade
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
