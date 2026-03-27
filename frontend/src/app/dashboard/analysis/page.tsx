"use client";

import { useState } from "react";
import axios from "axios";
import { analysisService } from "@/services/api";
import type { AnalysisResult } from "@/types";
import { Upload, FileText, Activity, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError("");
      setResult(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        setFile(droppedFile);
        setError("");
        setResult(null);
      } else {
        setError("Please upload a PDF file.");
      }
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setError("");

    try {
      const response = await analysisService.analyzePDF(file);
      setResult(response.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "Failed to analyze document.");
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
            AI Document Analysis
          </h1>
          <p className="text-muted-foreground mt-1">
            Upload financial reports, earnings calls, or research papers for AI-powered sentiment & metric extraction.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          {/* Upload Card */}
          <div className="glass-panel p-6 rounded-xl border border-white/10 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />
            
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <Upload className="w-5 h-5 text-emerald-400" />
              Upload PDF
            </h2>

            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
                file ? "border-emerald-500/50 bg-emerald-500/5" : "border-white/10 hover:border-white/20 hover:bg-white/5"
              )}
              onClick={() => document.getElementById("pdf-upload")?.click()}
            >
              <input
                id="pdf-upload"
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={handleFileChange}
              />
              
              <div className="flex flex-col items-center justify-center gap-3">
                <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center">
                  <FileText className={cn("w-6 h-6", file ? "text-emerald-400" : "text-muted-foreground")} />
                </div>
                {file ? (
                  <div>
                    <p className="font-medium text-emerald-400">{file.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                ) : (
                  <div>
                    <p className="font-medium text-white">Click or drag PDF here</p>
                    <p className="text-xs text-muted-foreground mt-1">Max 10MB</p>
                  </div>
                )}
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 rounded bg-red-500/10 border border-red-500/20 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className="w-full mt-6 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Activity className="w-4 h-4" />
                  Analyze Document
                </>
              )}
            </button>
          </div>
        </div>

        <div className="lg:col-span-2">
          {/* Result Card */}
          <div className="glass-panel p-6 rounded-xl border border-white/10 h-full min-h-[400px]">
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-6">
              <Activity className="w-5 h-5 text-purple-400" />
              Analysis Results
            </h2>

            {!result && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground py-20">
                <FileText className="w-12 h-12 mb-4 opacity-20" />
                <p>Upload a document to view AI analysis</p>
              </div>
            )}

            {loading && (
              <div className="h-full flex flex-col items-center justify-center text-emerald-400 py-20">
                <Loader2 className="w-10 h-10 animate-spin mb-4" />
                <p className="animate-pulse">Processing document via Neural Engine...</p>
              </div>
            )}

            {result && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Header info */}
                <div className="flex items-center justify-between pb-4 border-b border-white/10">
                  <div>
                    <h3 className="font-medium text-white">Document Scope</h3>
                    <p className="text-xl font-bold text-emerald-400 mt-1">{result.symbol || "General Analysis"}</p>
                  </div>
                  <div className="text-right">
                    <h3 className="font-medium text-white">AI Sentiment</h3>
                    <div className={cn(
                      "inline-flex items-center px-2.5 py-1 rounded text-xs font-semibold mt-1",
                      result.sentiment === "BULLISH" ? "bg-emerald-500/20 text-emerald-400" :
                      result.sentiment === "BEARISH" ? "bg-red-500/20 text-red-400" :
                      "bg-yellow-500/20 text-yellow-400"
                    )}>
                      {result.sentiment}
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-2">Executive Summary</h3>
                  <div className="p-4 rounded-lg bg-white/5 border border-white/5 text-sm leading-relaxed text-zinc-300">
                    {result.summary}
                  </div>
                </div>

                {/* Key Metrics */}
                {result.key_metrics && Object.keys(result.key_metrics).length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-3">Key Metrics Extracted</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {Object.entries(result.key_metrics).map(([key, value]) => (
                        <div key={key} className="p-3 rounded-lg bg-white/5 border border-white/5">
                          <p className="text-xs text-muted-foreground mb-1 capitalize">{key.replace(/_/g, " ")}</p>
                          <p className="font-medium text-white">{String(value)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
