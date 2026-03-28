"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { adminService, pipelineService } from "@/services/api";
import { useAuthStore } from "@/stores/useAuthStore";
import type {
  AdminUser,
  PipelineStatus,
  RevenueStats,
  UpgradeRequest,
} from "@/types";
import {
  Activity,
  BarChart3,
  CheckCircle,
  Clock,
  DollarSign,
  Loader2,
  Search,
  Shield,
  UserCheck,
  Users,
  XCircle,
  Zap,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

export default function AdminPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [revenue, setRevenue] = useState<RevenueStats | null>(null);
  const [queue, setQueue] = useState<UpgradeRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [pipelineState, setPipelineState] = useState<PipelineStatus | null>(
    null,
  );
  const [triggeringPipeline, setTriggeringPipeline] = useState(false);

  // Dialog
  const [showApprove, setShowApprove] = useState(false);
  const [approveEmail, setApproveEmail] = useState("");
  const [approvePlan, setApprovePlan] = useState("pro");
  const [approving, setApproving] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
    if (user?.role !== "admin" && user?.role !== "owner")
      router.push("/dashboard");
  }, [isAuthenticated, user, router]);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await adminService.getUsers(statusFilter);
      setUsers(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const fetchRevenue = useCallback(async () => {
    try {
      const { data } = await adminService.getRevenueStats();
      setRevenue(data);
    } catch {
      // silent
    }
  }, []);

  const fetchQueue = useCallback(async () => {
    try {
      const { data } = await adminService.getUpgradeQueue();
      setQueue(data);
    } catch {
      // silent
    }
  }, []);

  const fetchPipeline = useCallback(async () => {
    try {
      const { data } = await pipelineService.getStatus();
      setPipelineState(data);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && (user?.role === "admin" || user?.role === "owner")) {
      fetchUsers();
      fetchRevenue();
      fetchQueue();
      fetchPipeline();
    }
  }, [
    isAuthenticated,
    user,
    fetchUsers,
    fetchRevenue,
    fetchQueue,
    fetchPipeline,
  ]);

  const approveUser = async () => {
    setApproving(true);
    try {
      await adminService.approveUpgrade(approveEmail, approvePlan);
      setShowApprove(false);
      fetchUsers();
      fetchQueue();
    } catch {
      // silent
    } finally {
      setApproving(false);
    }
  };

  const triggerOptimize = async () => {
    setTriggeringPipeline(true);
    try {
      await pipelineService.triggerOptimize();
      fetchPipeline();
    } catch {
      // silent
    } finally {
      setTriggeringPipeline(false);
    }
  };

  const filteredUsers = users.filter((u) =>
    u.email.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  if (user?.role !== "admin" && user?.role !== "owner") return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between py-4 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-black bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tighter">
            Admin Panel
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            👑 Manage users & systems — <span className="text-chart-5 font-bold tracking-widest uppercase">Cloud Administration</span>
          </p>
        </div>
      </header>

      <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="glass-panel border border-white/10 p-1">
            <TabsTrigger
              value="overview"
              className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer"
            >
              <BarChart3 className="w-4 h-4 mr-1.5" /> Overview
            </TabsTrigger>
            <TabsTrigger
              value="users"
              className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer"
            >
              <Users className="w-4 h-4 mr-1.5" /> Users
            </TabsTrigger>
            <TabsTrigger
              value="queue"
              className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer"
            >
              <Clock className="w-4 h-4 mr-1.5" /> Queue
              {queue.length > 0 && (
                <Badge className="ml-1.5 bg-trade-down/20 text-trade-down px-1.5 text-[10px]">
                  {queue.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger
              value="pipeline"
              className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer"
            >
              <Zap className="w-4 h-4 mr-1.5" /> Pipeline
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {revenue ? (
                <>
                  <Card className="glass-panel border-white/10">
                    <CardContent className="p-5 text-center">
                      <Users className="w-6 h-6 mx-auto mb-2 text-primary" />
                      <p className="text-3xl font-bold">
                        {revenue.total_users}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Total Users
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="glass-panel border-white/10">
                    <CardContent className="p-5 text-center">
                      <DollarSign className="w-6 h-6 mx-auto mb-2 text-trade-up" />
                      <p className="text-3xl font-bold text-trade-up">
                        ${revenue.monthly_revenue_usd}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Monthly Revenue
                      </p>
                    </CardContent>
                  </Card>
                  {Object.entries(revenue.breakdown || {}).map(
                    ([role, count]) => (
                      <Card key={role} className="glass-panel border-white/10">
                        <CardContent className="p-5 text-center">
                          <Shield className="w-6 h-6 mx-auto mb-2 text-chart-5" />
                          <p className="text-3xl font-bold">{count}</p>
                          <p className="text-xs text-muted-foreground mt-1 capitalize">
                            {role}
                          </p>
                        </CardContent>
                      </Card>
                    ),
                  )}
                </>
              ) : (
                <div className="col-span-4 flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              )}
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>User Management</CardTitle>
                    <CardDescription>
                      {filteredUsers.length} users
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        placeholder="Cari email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 w-48 bg-white/5 border-white/10"
                      />
                    </div>
                    <Select
                      value={statusFilter}
                      onValueChange={(v) => setStatusFilter(v)}
                    >
                      <SelectTrigger className="w-28 bg-white/5 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="free">Free</SelectItem>
                        <SelectItem value="pro">Pro</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-white/10 hover:bg-transparent">
                        <TableHead>Email</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead className="text-right">Requests</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredUsers.map((u) => (
                        <TableRow
                          key={u._id}
                          className="border-white/5 hover:bg-white/5"
                        >
                          <TableCell className="font-medium">
                            {u.email}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className="capitalize border-primary/30 text-primary"
                            >
                              {u.role}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs">
                            {u.requests_today ?? 0}/
                            {u.daily_requests_limit ?? "∞"}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setApproveEmail(u.email);
                                setShowApprove(true);
                              }}
                              className="text-xs text-primary hover:text-primary"
                            >
                              <UserCheck className="w-3 h-3 mr-1" /> Upgrade
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Queue Tab */}
          <TabsContent value="queue">
            <Card className="glass-panel border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-chart-4" /> Upgrade Queue
                </CardTitle>
                <CardDescription>
                  {queue.length} permintaan menunggu
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {queue.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    Tidak ada permintaan.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-white/10 hover:bg-transparent">
                        <TableHead>Email</TableHead>
                        <TableHead>Requested Role</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {queue.map((req) => (
                        <TableRow
                          key={req._id || req.id}
                          className="border-white/5 hover:bg-white/5"
                        >
                          <TableCell className="font-medium">
                            {req.user_email}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="capitalize">
                              {req.requested_role}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              className={`${
                                req.status === "pending"
                                  ? "bg-chart-4/20 text-chart-4"
                                  : "bg-trade-up/20 text-trade-up"
                              }`}
                            >
                              {req.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {new Date(req.created_at).toLocaleDateString(
                              "id-ID",
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setApproveEmail(req.user_email);
                                  setApprovePlan(req.requested_role);
                                  setShowApprove(true);
                                }}
                                className="text-trade-up hover:text-trade-up"
                              >
                                <CheckCircle className="w-3.5 h-3.5" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-trade-down hover:text-trade-down"
                              >
                                <XCircle className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Pipeline Tab */}
          <TabsContent value="pipeline">
            <Card className="glass-panel border-white/10 max-w-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-400" /> AI
                  Retraining Pipeline
                </CardTitle>
                <CardDescription>
                  Monitor and trigger neural engine optimizations and nightly
                  training jobs.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 bg-white/5 border border-white/10 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                      Current Status
                    </span>
                    {pipelineState ? (
                      <Badge
                        className={
                          pipelineState.status === "running"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : pipelineState.status === "failed"
                              ? "bg-red-500/20 text-red-500"
                              : "bg-white/10 text-white"
                        }
                      >
                        {pipelineState.status}
                      </Badge>
                    ) : (
                      <Badge className="bg-white/10 text-white">UNKNOWN</Badge>
                    )}
                  </div>

                  {pipelineState?.status === "running" && (
                    <div className="mt-4 space-y-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-emerald-400 animate-pulse">
                          {pipelineState.message ||
                            "Optimization in progress..."}
                        </span>
                        <span>{pipelineState.progress}%</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-1.5">
                        <div
                          className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${pipelineState.progress}%` }}
                        />
                      </div>
                      {pipelineState.eta && (
                        <p className="text-xs text-muted-foreground">
                          ETA: {pipelineState.eta}
                        </p>
                      )}
                    </div>
                  )}

                  {pipelineState?.status !== "running" && (
                    <div className="mt-4 text-sm text-muted-foreground">
                      <p>Pipeline is idle. Ready for manual triggers.</p>
                      {pipelineState?.last_run && (
                        <p className="mt-1">
                          Last run:{" "}
                          {new Date(pipelineState.last_run).toLocaleString()}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-white/10">
                  <Button
                    onClick={triggerOptimize}
                    disabled={
                      triggeringPipeline || pipelineState?.status === "running"
                    }
                    className="w-full sm:w-auto bg-gradient-to-r from-emerald-600 to-purple-600 hover:from-emerald-500 hover:to-purple-500 text-white border-0"
                  >
                    {triggeringPipeline ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Zap className="w-4 h-4 mr-2" />
                    )}
                    Trigger Hyper-Optimization
                  </Button>
                  <p className="text-xs text-muted-foreground mt-3">
                    Warning: Manual trigger will immediately fetch new market
                    conditions and adjust neural nets. This is extremely
                    computationally expensive.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Approve Dialog */}
        <Dialog open={showApprove} onOpenChange={setShowApprove}>
          <DialogContent className="glass-panel border-white/10">
            <DialogHeader>
              <DialogTitle>Upgrade User</DialogTitle>
              <DialogDescription>
                Upgrade {approveEmail} ke plan baru
              </DialogDescription>
            </DialogHeader>
            <Select value={approvePlan} onValueChange={setApprovePlan}>
              <SelectTrigger className="bg-white/5 border-white/10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pro">Pro</SelectItem>
                <SelectItem value="premium">Premium</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowApprove(false)}
                className="border-white/10"
              >
                Batal
              </Button>
              <Button
                onClick={approveUser}
                disabled={approving}
                className="bg-trade-up/20 text-trade-up hover:bg-trade-up/30"
              >
                {approving ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <CheckCircle className="w-4 h-4 mr-2" />
                )}
                Approve
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
    </div>
  );
}
