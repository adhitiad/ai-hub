"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { ownerService } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Crown,
  FolderTree,
  FileText,
  Terminal,
  Brain,
  RefreshCw,
  Loader2,
  Play,
  Activity,
  HardDrive,
  ChevronRight,
  Folder,
  File,
} from "lucide-react";

interface FileNode {
  name: string;
  type: "file" | "dir";
  children?: FileNode[];
  path?: string;
}

export default function OwnerPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  // Logs
  const [logs, setLogs] = useState<string[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);

  // File tree
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState("");
  const [fileLoading, setFileLoading] = useState(false);

  // Actions
  const [retraining, setRetraining] = useState(false);
  const [restarting, setRestarting] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  // Financial
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
    if (user?.role !== "owner") router.push("/dashboard");
  }, [isAuthenticated, user, router]);

  const fetchLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const { data } = await ownerService.getLogsStream();
      if (Array.isArray(data)) setLogs(data.map(String));
      else if (typeof data === "string") setLogs(data.split("\n"));
      else setLogs([JSON.stringify(data, null, 2)]);
    } catch {
      setLogs(["❌ Gagal memuat logs"]);
    } finally {
      setLogsLoading(false);
    }
  }, []);

  const fetchFileTree = useCallback(async () => {
    try {
      const { data } = await ownerService.getFileTree();
      setFileTree(data.tree || data || []);
    } catch {
      setFileTree([]);
    }
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const { data } = await ownerService.getFinancialHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && user?.role === "owner") {
      fetchLogs();
      fetchFileTree();
      fetchHealth();
    }
  }, [isAuthenticated, user, fetchLogs, fetchFileTree, fetchHealth]);

  const readFile = async (path: string) => {
    setSelectedFile(path);
    setFileLoading(true);
    try {
      const { data } = await ownerService.readFile(path);
      setFileContent(typeof data === "string" ? data : data.content || JSON.stringify(data, null, 2));
    } catch {
      setFileContent("❌ Gagal membaca file");
    } finally {
      setFileLoading(false);
    }
  };

  const triggerRetrain = async () => {
    setRetraining(true);
    setActionMsg(null);
    try {
      await ownerService.triggerRetrain();
      setActionMsg("✅ Retraining dimulai!");
    } catch {
      setActionMsg("❌ Gagal memulai retraining");
    } finally {
      setRetraining(false);
    }
  };

  const triggerRestart = async () => {
    setRestarting(true);
    setActionMsg(null);
    try {
      await ownerService.restartBot();
      setActionMsg("✅ Bot di-restart!");
    } catch {
      setActionMsg("❌ Gagal me-restart bot");
    } finally {
      setRestarting(false);
    }
  };

  const renderTree = (nodes: FileNode[], depth = 0) =>
    nodes.map((node) => (
      <div key={node.path || node.name}>
        <button
          onClick={() => node.type === "file" && readFile(node.path || node.name)}
          className={`w-full flex items-center gap-2 py-1.5 px-2 text-sm rounded hover:bg-white/5 transition-colors text-left cursor-pointer ${
            selectedFile === (node.path || node.name) ? "bg-primary/10 text-primary" : "text-muted-foreground"
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {node.type === "dir" ? (
            <>
              <ChevronRight className="w-3 h-3 shrink-0" />
              <Folder className="w-3.5 h-3.5 text-chart-4 shrink-0" />
            </>
          ) : (
            <>
              <span className="w-3" />
              <File className="w-3.5 h-3.5 text-chart-3 shrink-0" />
            </>
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {node.children && renderTree(node.children, depth + 1)}
      </div>
    ));

  if (user?.role !== "owner") return null;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-chart-4 to-trade-down bg-clip-text text-transparent">
              Owner Panel
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              🔐 System control — <span className="text-chart-5">オーナー</span>
            </p>
          </div>
          <Badge variant="outline" className="border-chart-4/30 text-chart-4">
            <Crown className="w-3 h-3 mr-1" /> Super Admin
          </Badge>
        </div>

        <Tabs defaultValue="actions" className="space-y-6">
          <TabsList className="glass-panel border border-white/10 p-1">
            <TabsTrigger value="actions" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <Activity className="w-4 h-4 mr-1.5" /> Actions
            </TabsTrigger>
            <TabsTrigger value="files" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <FolderTree className="w-4 h-4 mr-1.5" /> Files
            </TabsTrigger>
            <TabsTrigger value="logs" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <Terminal className="w-4 h-4 mr-1.5" /> Logs
            </TabsTrigger>
            <TabsTrigger value="health" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer">
              <HardDrive className="w-4 h-4 mr-1.5" /> Health
            </TabsTrigger>
          </TabsList>

          {/* Actions Tab */}
          <TabsContent value="actions">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="glass-panel border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Brain className="w-5 h-5 text-chart-5" /> AI Retraining
                  </CardTitle>
                  <CardDescription>Mulai proses retraining model AI</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={triggerRetrain}
                    disabled={retraining}
                    className="bg-chart-5/20 text-chart-5 hover:bg-chart-5/30 w-full"
                  >
                    {retraining ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                    Start Retraining
                  </Button>
                </CardContent>
              </Card>

              <Card className="glass-panel border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <RefreshCw className="w-5 h-5 text-chart-4" /> Bot Restart
                  </CardTitle>
                  <CardDescription>Restart bot trading logic</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={triggerRestart}
                    disabled={restarting}
                    className="bg-chart-4/20 text-chart-4 hover:bg-chart-4/30 w-full"
                  >
                    {restarting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                    Restart Bot
                  </Button>
                </CardContent>
              </Card>
            </div>
            {actionMsg && (
              <p className="mt-4 text-sm text-center">{actionMsg}</p>
            )}
          </TabsContent>

          {/* Files Tab */}
          <TabsContent value="files">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4" style={{ height: 500 }}>
              {/* File Tree */}
              <Card className="glass-panel border-white/10 overflow-hidden">
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <FolderTree className="w-4 h-4 text-chart-4" /> Explorer
                  </CardTitle>
                </CardHeader>
                <ScrollArea className="h-[430px]">
                  <CardContent className="p-2">
                    {fileTree.length === 0 ? (
                      <p className="text-xs text-muted-foreground text-center py-6">Tidak ada data.</p>
                    ) : (
                      renderTree(fileTree)
                    )}
                  </CardContent>
                </ScrollArea>
              </Card>

              {/* File Content */}
              <Card className="md:col-span-2 glass-panel border-white/10 overflow-hidden">
                <CardHeader className="py-3 px-4 border-b border-white/10">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <FileText className="w-4 h-4 text-chart-3" />
                    {selectedFile ? selectedFile.split("/").pop() : "Pilih file..."}
                  </CardTitle>
                </CardHeader>
                <ScrollArea className="h-[430px]">
                  <CardContent className="p-0">
                    {fileLoading ? (
                      <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-6 h-6 animate-spin text-primary" />
                      </div>
                    ) : (
                      <pre className="p-4 text-xs font-mono text-muted-foreground whitespace-pre-wrap leading-relaxed">
                        {fileContent || "// Pilih file dari explorer di sebelah kiri"}
                      </pre>
                    )}
                  </CardContent>
                </ScrollArea>
              </Card>
            </div>
          </TabsContent>

          {/* Logs Tab */}
          <TabsContent value="logs">
            <Card className="glass-panel border-white/10">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Terminal className="w-5 h-5 text-trade-up" /> System Logs
                  </CardTitle>
                  <CardDescription>{logs.length} entries</CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={fetchLogs} disabled={logsLoading}>
                  <RefreshCw className={`w-4 h-4 ${logsLoading ? "animate-spin" : ""}`} />
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[400px]">
                  <div className="p-4 font-mono text-xs space-y-0.5">
                    {logs.map((line, i) => (
                      <div
                        key={i}
                        className={`py-0.5 ${
                          line.includes("ERROR") || line.includes("❌")
                            ? "text-trade-down"
                            : line.includes("WARNING") || line.includes("⚠")
                            ? "text-chart-4"
                            : line.includes("INFO") || line.includes("✅")
                            ? "text-trade-up"
                            : "text-muted-foreground"
                        }`}
                      >
                        <span className="text-muted-foreground/40 mr-2 select-none">{String(i + 1).padStart(4, " ")}</span>
                        {line}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Health Tab */}
          <TabsContent value="health">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <HardDrive className="w-5 h-5 text-chart-3" /> Financial & System Health
                </CardTitle>
              </CardHeader>
              <CardContent>
                {health ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(health).map(([key, value]) => (
                      <div key={key} className="p-4 rounded-lg bg-white/5 border border-white/10 text-center">
                        <p className="text-xs text-muted-foreground mb-1 capitalize">{key.replace(/_/g, " ")}</p>
                        <p className="text-lg font-bold font-mono">
                          {typeof value === "number" ? value.toLocaleString() : String(value)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
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
