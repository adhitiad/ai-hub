"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { LoginSchema, type LoginInput, type LoginResponse } from "@/types";
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/useAuthStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Zap, Loader2, Eye, EyeOff, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(LoginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: LoginInput) => {
    try {
      setLoading(true);
      setServerError("");
      const res = await api.post<LoginResponse>("/auth/login", values);

      if (res.data.status === "success") {
        const { user } = res.data;
        login(
          { email: user.email, role: user.role },
          user.api_key
        );
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err
      ) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setServerError(
          axiosErr.response?.data?.detail ?? "Login gagal. Coba lagi."
        );
      } else {
        setServerError("Koneksi ke server gagal.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4">
      {/* Animated background blobs */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/4 -left-32 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 rounded-full bg-purple-600/10 blur-3xl animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-pink-500/5 blur-3xl animate-pulse" style={{ animationDelay: "2s" }} />
      </div>

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <Card className="w-full max-w-md glass-panel border-white/10 overflow-hidden">
        {/* Glowing top border */}
        <div className="h-0.5 bg-gradient-to-r from-transparent via-emerald-500 to-transparent" />

        <CardHeader className="text-center space-y-4 pt-8 pb-2">
          {/* Logo */}
          <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-purple-600 flex items-center justify-center shadow-xl shadow-emerald-500/20 relative">
            <Zap className="w-8 h-8 text-white" />
            <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 animate-pulse border-2 border-background" />
          </div>
          <div>
            <CardTitle className="text-xl font-bold bg-gradient-to-r from-emerald-400 via-white to-purple-400 bg-clip-text text-transparent">
              Welcome Back, Trader
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              ニューラルエンジンにログイン — Login to Neural Engine
            </p>
          </div>
        </CardHeader>

        <CardContent className="space-y-5 px-8 pb-8">
          {serverError && (
            <div className="flex items-center gap-2 rounded-lg bg-trade-down/10 border border-trade-down/20 px-3 py-2 text-xs text-trade-down">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {serverError}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs text-muted-foreground uppercase tracking-wider">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="trader@example.com"
                className="bg-white/5 border-white/10 focus:border-primary/50 focus:ring-primary/20 placeholder:text-muted-foreground/40"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-[11px] text-trade-down">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs text-muted-foreground uppercase tracking-wider">
                Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="bg-white/5 border-white/10 focus:border-primary/50 focus:ring-primary/20 pr-10 placeholder:text-muted-foreground/40"
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((p) => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-[11px] text-trade-down">{errors.password.message}</p>
              )}
            </div>

            {/* Submit */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold shadow-lg shadow-emerald-500/20 transition-all duration-300 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : (
                "Login"
              )}
            </Button>
          </form>

          {/* Register link */}
          <p className="text-center text-xs text-muted-foreground">
            Belum punya akun?{" "}
            <Link
              href="/register"
              className="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors"
            >
              Register
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
