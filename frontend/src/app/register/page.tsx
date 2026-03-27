"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { RegisterSchema, type RegisterInput, type RegisterResponse } from "@/types";
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/useAuthStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Zap, Loader2, Eye, EyeOff, AlertCircle, Copy, Check } from "lucide-react";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiKeyResult, setApiKeyResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterInput>({
    resolver: zodResolver(RegisterSchema),
    defaultValues: { email: "", password: "", confirmPassword: "" },
  });

  const onSubmit = async (values: RegisterInput) => {
    try {
      setLoading(true);
      setServerError("");
      const res = await api.post<RegisterResponse>("/auth/register", {
        email: values.email,
        password: values.password,
      });

      if (res.data.status === "success") {
        setApiKeyResult(res.data.api_key);
        // Auto-login to the store
        login(
          { email: values.email, role: "free" },
          res.data.api_key
        );
      }
    } catch (err: unknown) {
      if (
        typeof err === "object" &&
        err !== null &&
        "response" in err
      ) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setServerError(
          axiosErr.response?.data?.detail ?? "Registrasi gagal."
        );
      } else {
        setServerError("Koneksi ke server gagal.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopyKey = async () => {
    if (!apiKeyResult) return;
    await navigator.clipboard.writeText(apiKeyResult);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden px-4">
      {/* Animated background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/3 -left-20 w-80 h-80 rounded-full bg-purple-600/10 blur-3xl animate-pulse" />
        <div className="absolute bottom-1/3 -right-20 w-80 h-80 rounded-full bg-emerald-500/10 blur-3xl animate-pulse" style={{ animationDelay: "1.5s" }} />
      </div>

      <div
        className="absolute inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <Card className="w-full max-w-md glass-panel border-white/10 overflow-hidden">
        <div className="h-0.5 bg-gradient-to-r from-transparent via-purple-500 to-transparent" />

        <CardHeader className="text-center space-y-4 pt-8 pb-2">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-500 flex items-center justify-center shadow-xl shadow-purple-500/20 relative">
            <Zap className="w-8 h-8 text-white" />
            <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-pink-400 animate-pulse border-2 border-background" />
          </div>
          <div>
            <CardTitle className="text-xl font-bold bg-gradient-to-r from-purple-400 via-white to-pink-400 bg-clip-text text-transparent">
              Bergabung Sekarang
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              新規登録 — Create Your Trading Account
            </p>
          </div>
        </CardHeader>

        <CardContent className="space-y-5 px-8 pb-8">
          {/* API Key Result Screen */}
          {apiKeyResult ? (
            <div className="space-y-4">
              <div className="rounded-lg bg-trade-up/10 border border-trade-up/20 px-4 py-3 text-center">
                <p className="text-xs text-trade-up font-medium mb-2">
                  ✨ Registrasi Berhasil!
                </p>
                <p className="text-[11px] text-muted-foreground mb-3">
                  Simpan API Key berikut. Ini hanya ditampilkan <strong>SEKALI</strong>.
                </p>
                <div className="flex items-center gap-2 bg-black/30 rounded-lg p-3 overflow-hidden">
                  <code className="text-[11px] text-trade-up font-mono truncate flex-1">
                    {apiKeyResult}
                  </code>
                  <button
                    onClick={handleCopyKey}
                    className="shrink-0 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  >
                    {copied ? <Check className="w-4 h-4 text-trade-up" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <Button
                onClick={() => router.push("/dashboard")}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-semibold shadow-lg shadow-purple-500/20 cursor-pointer"
              >
                Masuk ke Dashboard →
              </Button>
            </div>
          ) : (
            <>
              {serverError && (
                <div className="flex items-center gap-2 rounded-lg bg-trade-down/10 border border-trade-down/20 px-3 py-2 text-xs text-trade-down">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {serverError}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

                <div className="space-y-1.5">
                  <Label htmlFor="confirmPassword" className="text-xs text-muted-foreground uppercase tracking-wider">
                    Konfirmasi Password
                  </Label>
                  <Input
                    id="confirmPassword"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="bg-white/5 border-white/10 focus:border-primary/50 focus:ring-primary/20 placeholder:text-muted-foreground/40"
                    {...register("confirmPassword")}
                  />
                  {errors.confirmPassword && (
                    <p className="text-[11px] text-trade-down">{errors.confirmPassword.message}</p>
                  )}
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-semibold shadow-lg shadow-purple-500/20 transition-all duration-300 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    "Register"
                  )}
                </Button>
              </form>

              <p className="text-center text-xs text-muted-foreground">
                Sudah punya akun?{" "}
                <Link
                  href="/login"
                  className="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors"
                >
                  Login
                </Link>
              </p>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
