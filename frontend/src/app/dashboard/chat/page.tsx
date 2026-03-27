"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { chatService } from "@/services/api";
import type { ChatMessage } from "@/types";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import {
  MessageCircle,
  Send,
  Loader2,
  Bot,
  User,
  Sparkles,
  Trash2,
  Copy,
  Check,
} from "lucide-react";

export default function ChatPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [symbol, setSymbol] = useState("");
  const [sending, setSending] = useState(false);
  const [copied, setCopied] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const msg = input.trim();
    if (!msg || sending) return;

    const userMsg: ChatMessage = {
      role: "user",
      content: msg,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const { data } = await chatService.ask(msg, symbol || undefined);
      const aiMsg: ChatMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Gagal mendapatkan respons. Coba lagi nanti.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyText = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  };

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 flex flex-col h-screen">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 glass-panel flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                AI Trading Assistant
              </h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-chart-4" /> RAG-Powered · <span className="text-chart-5">AIアシスタント</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Context symbol (opsional)"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs w-36 outline-none focus:border-primary/40"
            />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setMessages([])}
                    className="text-muted-foreground hover:text-trade-down"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Clear chat</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 px-6">
          <div className="max-w-3xl mx-auto py-6 space-y-6">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center mb-6 border border-white/10">
                  <MessageCircle className="w-10 h-10 text-purple-400" />
                </div>
                <h2 className="text-xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Konnichiwa, Trader! 🎌
                </h2>
                <p className="text-sm text-muted-foreground max-w-md">
                  Tanyakan apa saja tentang pasar, saham, crypto, atau strategi trading.
                  AI kami akan mencari jawabannya dengan teknologi RAG.
                </p>
                <div className="flex gap-2 mt-6 flex-wrap justify-center">
                  {[
                    "Analisis BBCA hari ini",
                    "Apa itu support dan resistance?",
                    "Kapan waktu terbaik trading forex?",
                    "Perbandingan BTC vs ETH",
                  ].map((q) => (
                    <Button
                      key={q}
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setInput(q);
                      }}
                      className="text-xs border-white/10 hover:border-primary/30 hover:bg-primary/5"
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
              >
                {msg.role === "assistant" && (
                  <Avatar className="w-8 h-8 shrink-0 border border-purple-500/30">
                    <AvatarFallback className="bg-gradient-to-br from-purple-600 to-pink-600 text-white text-xs">
                      AI
                    </AvatarFallback>
                  </Avatar>
                )}

                <Card className={`max-w-[80%] border-0 shadow-none ${
                  msg.role === "user"
                    ? "bg-primary/15 border border-primary/20"
                    : "bg-white/5 border border-white/10"
                }`}>
                  <CardContent className="p-4">
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    {msg.sources && (
                      <div className="mt-3 pt-3 border-t border-white/10">
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Sources</p>
                        <p className="text-xs text-muted-foreground">{msg.sources}</p>
                      </div>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[10px] text-muted-foreground">
                        {msg.timestamp?.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      {msg.role === "assistant" && (
                        <button
                          onClick={() => copyText(msg.content, i)}
                          className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                        >
                          {copied === i ? <Check className="w-3 h-3 text-trade-up" /> : <Copy className="w-3 h-3" />}
                        </button>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {msg.role === "user" && (
                  <Avatar className="w-8 h-8 shrink-0 border border-emerald-500/30">
                    <AvatarFallback className="bg-gradient-to-br from-emerald-600 to-cyan-600 text-white text-xs">
                      {user?.email?.[0]?.toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex gap-3">
                <Avatar className="w-8 h-8 shrink-0 border border-purple-500/30">
                  <AvatarFallback className="bg-gradient-to-br from-purple-600 to-pink-600 text-white text-xs">
                    AI
                  </AvatarFallback>
                </Avatar>
                <Card className="bg-white/5 border border-white/10">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                      <span className="text-sm text-muted-foreground animate-pulse">
                        AI sedang berpikir...
                      </span>
                      <Badge variant="outline" className="text-[9px] border-purple-500/30 text-purple-400">
                        RAG
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="px-6 py-4 border-t border-white/10 glass-panel shrink-0">
          <div className="max-w-3xl mx-auto flex gap-3">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tanya AI tentang pasar, sinyal, atau strategi..."
              className="min-h-[48px] max-h-32 resize-none bg-white/5 border-white/10 focus-visible:ring-purple-500/30 rounded-xl"
              rows={1}
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || sending}
              className="shrink-0 bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 text-white rounded-xl px-5"
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
