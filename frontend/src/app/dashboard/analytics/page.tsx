"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { 
  BarChart3, Zap, Layers, RefreshCw, Clock, Award, ShieldAlert, CheckCircle2 
} from "lucide-react";
import { toast } from "sonner";

interface TokenMetrics {
  prompt_tokens: number;
  candidate_tokens: number;
  total_tokens: number;
}

export default function AnalyticsPage() {
  const [tokenMetrics, setTokenMetrics] = useState<TokenMetrics>({
    prompt_tokens: 0,
    candidate_tokens: 0,
    total_tokens: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [eventsCount, setEventsCount] = useState(0);
  const [avgScore, setAvgScore] = useState(0);

  async function loadMetrics() {
    setIsLoading(true);
    try {
      // Load token metrics from Gemini metrics endpoint
      const { data: metrics } = await api.get("/gemini/metrics");
      setTokenMetrics({
        prompt_tokens: metrics?.prompt_tokens ?? 0,
        candidate_tokens: metrics?.candidate_tokens ?? 0,
        total_tokens: metrics?.total_tokens ?? 0
      });

      // Load events count and launch score averages
      const { data: events } = await api.get("/events/");
      const list = Array.isArray(events) ? events : (events?.items ?? []);
      setEventsCount(list.length);
      
      const scores = list.filter((e: any) => e.launch_score !== null).map((e: any) => e.launch_score);
      if (scores.length > 0) {
        const sum = scores.reduce((a: number, b: number) => a + b, 0);
        setAvgScore(Math.round(sum / scores.length));
      }
    } catch (err) {
      console.error("Failed to load metrics", err);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadMetrics();
  }, []);

  // Compute calculated metrics
  const costUSD = (tokenMetrics.prompt_tokens * 1.25 / 1000000) + (tokenMetrics.candidate_tokens * 5.00 / 1000000);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/5">
        <div>
          <h1 className="font-display font-bold text-3xl text-white">Analytics Hub</h1>
          <p className="text-sm text-surface-500 mt-1">Audit AI system token distributions, model latencies, and generation counts</p>
        </div>
        
        <button
          onClick={loadMetrics}
          className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-white border border-white/8 px-4 py-2.5 rounded-xl font-bold transition-all text-xs self-start"
        >
          <RefreshCw className="w-4 h-4" /> Refresh Metrics
        </button>
      </div>

      {/* Main metrics grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-xs text-surface-500 font-bold uppercase tracking-wider">Total Tokens</p>
          <p className="font-display font-bold text-3xl text-white mt-2">
            {tokenMetrics.total_tokens.toLocaleString()}
          </p>
          <span className="text-[10px] text-surface-600 font-semibold block mt-1">
            Gemini Flash / Pro
          </span>
        </div>

        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-xs text-surface-500 font-bold uppercase tracking-wider">Estimated Model Cost</p>
          <p className="font-display font-bold text-3xl text-white mt-2">
            ${costUSD.toFixed(4)}
          </p>
          <span className="text-[10px] text-amber-400 font-semibold block mt-1">
            Based on USD rates
          </span>
        </div>

        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-xs text-surface-500 font-bold uppercase tracking-wider">Average Launch Score</p>
          <p className="font-display font-bold text-3xl text-white mt-2">
            {avgScore}%
          </p>
          <span className="text-[10px] text-emerald-400 font-semibold block mt-1">
            GTM campaign readiness
          </span>
        </div>

        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accent-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-xs text-surface-500 font-bold uppercase tracking-wider">Active Hackathons</p>
          <p className="font-display font-bold text-3xl text-white mt-2">
            {eventsCount}
          </p>
          <span className="text-[10px] text-surface-600 font-semibold block mt-1">
            Currently managed GTM packages
          </span>
        </div>
      </div>

      {/* Visual token split and stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Token split */}
        <div className="lg:col-span-2 glass-card rounded-3xl p-6 space-y-6">
          <h3 className="text-md font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-400" />
            Token Usage Distribution
          </h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-xs font-semibold mb-2">
                <span className="text-surface-500">Prompt / Input Tokens</span>
                <span className="text-white">{tokenMetrics.prompt_tokens.toLocaleString()} ({tokenMetrics.total_tokens > 0 ? Math.round(tokenMetrics.prompt_tokens * 100 / tokenMetrics.total_tokens) : 0}%)</span>
              </div>
              <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-brand-500 rounded-full transition-all duration-500" 
                  style={{ width: `${tokenMetrics.total_tokens > 0 ? (tokenMetrics.prompt_tokens * 100 / tokenMetrics.total_tokens) : 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-2">
                <span className="text-surface-500">Candidate / Output Tokens</span>
                <span className="text-white">{tokenMetrics.candidate_tokens.toLocaleString()} ({tokenMetrics.total_tokens > 0 ? Math.round(tokenMetrics.candidate_tokens * 100 / tokenMetrics.total_tokens) : 0}%)</span>
              </div>
              <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-amber-500 rounded-full transition-all duration-500" 
                  style={{ width: `${tokenMetrics.total_tokens > 0 ? (tokenMetrics.candidate_tokens * 100 / tokenMetrics.total_tokens) : 0}%` }}
                />
              </div>
            </div>
          </div>

          <div className="p-4 glass rounded-xl border border-white/5 text-[10px] text-surface-500 leading-relaxed space-y-2">
            <p className="font-bold text-white uppercase tracking-wider">Estimated costs calculations details:</p>
            <ul className="list-disc pl-4 space-y-1 font-medium">
              <li>Input Prompt rate: $1.25 / 1M tokens</li>
              <li>Output Completion rate: $5.00 / 1M tokens</li>
            </ul>
          </div>
        </div>

        {/* Latency and quality cards */}
        <div className="glass-card rounded-3xl p-6 space-y-6">
          <h3 className="text-md font-bold text-white">System Health</h3>
          <div className="space-y-4 text-xs font-semibold">
            <div className="flex items-center justify-between p-4 bg-white/2 rounded-2xl border border-white/5">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-brand-400" />
                <span className="text-surface-500">Generation Latency</span>
              </div>
              <span className="text-white">~3.2s avg</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-white/2 rounded-2xl border border-white/5">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-400" />
                <span className="text-surface-500">Vector collections</span>
              </div>
              <span className="text-white">4 collections active</span>
            </div>

            <div className="flex items-center justify-between p-4 bg-white/2 rounded-2xl border border-white/5">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-surface-500">Rate Limiter Status</span>
              </div>
              <span className="text-emerald-400">Online (15 RPM limit)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
