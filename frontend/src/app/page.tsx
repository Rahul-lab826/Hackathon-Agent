"use client";
import Link from "next/link";
import {
  Zap, Brain, Rocket, BarChart3, Mail, Calendar,
  ChevronRight, Sparkles, ArrowRight, Check, Globe,
  Users, Clock, Award
} from "lucide-react";

const AGENTS = [
  { name: "Brand Agent",     icon: Sparkles,  color: "#3d5eff", desc: "Crafts event name, catchy tagline, and cohesive visual identity guidelines." },
  { name: "Structure Agent", icon: BarChart3,  color: "#8b5cf6", desc: "Constructs hour-by-hour timeline schedule and custom judging rubrics." },
  { name: "Content Agent",   icon: Brain,      color: "#d946ef", desc: "Drafts landing page copy, headings, and detailed FAQ sections." },
  { name: "Marketing Agent", icon: Globe,      color: "#f59e0b", desc: "Generates tailored social posts across LinkedIn, Twitter, and Slack." },
  { name: "Email Agent",     icon: Mail,       color: "#10b981", desc: "Prepares ready-to-send invite drafts and sponsor partnership templates." },
  { name: "Execution Agent", icon: Rocket,     color: "#ef4444", desc: "Compiles a week-by-week operational checklist and risk mitigation plans." },
];

const STATS = [
  { value: "8",    label: "AI Agents",           icon: Brain   },
  { value: "60s",  label: "Average Generation",  icon: Clock   },
  { value: "100+", label: "Content Pieces",       icon: Sparkles },
  { value: "10",   label: "Connected Channels",  icon: Globe   },
];

const FEATURES = [
  { icon: Zap,      title: "Instant Package Compile", desc: "Create a complete Go-To-Market package in under 60 seconds. No blank pages, no copy-paste errors." },
  { icon: Brain,    title: "Qdrant Memory Layer",     desc: "Learns from your target audience preferences, previous events, and organizers feedback."  },
  { icon: Calendar, title: "Google Workspace MCP",    desc: "Exposes 40 CRUD actions. Autopilot Gmail drafts, Calendar invites, and Sheets logs."       },
  { icon: Users,    title: "Lyzr Orchestrator",       desc: "Runs sequential pipelines with background retry queues and robust error recovery logs."   },
  { icon: Award,    title: "Launch Readiness Score",  desc: "Automatically audits all compiled assets and scores launch viability index."              },
  { icon: Globe,    title: "Document Export Module",  desc: "Instantly download compiled packages as styled PDF, Word DOCX, CSV sheets, and HTML."      },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen w-full bg-[#080914] text-[#e8eaf0] font-sans antialiased overflow-x-hidden">
      
      {/* ── Background Glow Details ────────────────────────── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-brand-600/10 rounded-full blur-[120px] opacity-70" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-accent-600/10 rounded-full blur-[100px] opacity-60" />
      </div>

      {/* ── Navigation Bar ──────────────────────────────────── */}
      <nav className="relative z-50 flex items-center justify-between px-6 md:px-12 py-5 bg-[#0b0d1e]/85 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-brand flex items-center justify-center shadow-glow-brand">
            <Rocket className="w-5 h-5 text-white" />
          </div>
          <span className="font-display font-extrabold text-xl text-white tracking-tight">
            HackLaunch <span className="gradient-text">AI</span>
          </span>
        </div>
        
        <div className="hidden md:flex items-center gap-8 text-sm text-surface-400 font-medium">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#agents"   className="hover:text-white transition-colors">AI Team</a>
          <a href="#cta"      className="hover:text-white transition-colors">Pricing</a>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-surface-300 hover:text-white transition-colors font-medium px-4 py-2">
            Sign In
          </Link>
          <Link href="/register" className="flex items-center gap-2 text-sm bg-gradient-brand text-white px-5 py-2.5 rounded-xl font-bold btn-lift shadow-glow-brand">
            Get Started <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      {/* ── Main Landing Layout Flow ───────────────────────── */}
      <main className="relative z-10 flex flex-col w-full items-center">
        
        {/* ── Hero Section ──────────────────────────────────── */}
        <section className="flex flex-col items-center text-center px-6 pt-20 pb-16 max-w-6xl w-full">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-brand-500/20 bg-brand-950/20 text-brand-300 text-xs font-semibold mb-8 backdrop-blur-md">
            <Sparkles className="w-4 h-4 text-brand-400" />
            Powered by Gemini Pro & Flash · 8 Autonomous Agents
          </div>

          <h1 className="font-display font-extrabold text-4xl sm:text-6xl md:text-7xl text-white leading-tight tracking-tight max-w-4xl mb-6">
            Your Hackathon GTM, <br />
            <span className="gradient-text glow-text-brand">Fully Compiled</span> in 60s.
          </h1>

          <p className="text-surface-400 text-lg md:text-xl max-w-2xl mb-10 leading-relaxed">
            From initial idea to fully generated event copy, schedule, social campaigns, 
            weekly operations checklist, and budget analysis — all structured and indexed.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center w-full mb-20">
            <Link href="/register" className="flex items-center gap-3 bg-gradient-brand text-white px-8 py-4 rounded-xl text-lg font-bold btn-lift shadow-glow-brand group w-full sm:w-auto justify-center">
              Launch Your GTM Package
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link href="/login" className="flex items-center gap-2 border border-white/10 bg-white/5 text-surface-200 px-8 py-4 rounded-xl text-lg font-semibold hover:border-white/20 hover:text-white hover:bg-white/10 transition-all w-full sm:w-auto justify-center">
              Sign In
            </Link>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl w-full p-8 border border-white/5 bg-[#0d0f22]/70 rounded-3xl backdrop-blur-md">
            {STATS.map((s, index) => (
              <div key={index} className="flex flex-col items-center justify-center p-4 text-center">
                <span className="font-display font-extrabold text-3xl md:text-4xl gradient-text">{s.value}</span>
                <span className="text-[10px] md:text-xs text-surface-500 font-bold uppercase tracking-wider mt-2">{s.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* ── Agents Grid Section ────────────────────────────── */}
        <section id="agents" className="w-full flex justify-center py-24 bg-[#0a0c1a]/60 border-y border-white/5 px-6">
          <div className="max-w-6xl w-full">
            <div className="text-center mb-16">
              <h2 className="font-display font-extrabold text-3xl md:text-5xl text-white mb-4">
                Meet Your Autonomous AI Team
              </h2>
              <p className="text-surface-400 text-base md:text-lg max-w-xl mx-auto">
                Each agent is custom-prompted to handle details of your go-to-market. 
                They run in sequence, passing outputs automatically.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {AGENTS.map((agent, i) => (
                <div key={i} className="flex flex-col justify-between p-6 rounded-2xl border border-white/5 bg-[#0d0f22]/80 hover:border-brand-500/20 hover:bg-[#11142e] transition-all duration-300 group shadow-md">
                  <div>
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-6"
                         style={{ background: `${agent.color}15`, border: `1px solid ${agent.color}25` }}>
                      <agent.icon className="w-6 h-6" style={{ color: agent.color }} />
                    </div>
                    <h3 className="font-display font-bold text-white text-lg mb-2">{agent.name}</h3>
                    <p className="text-surface-400 text-sm leading-relaxed mb-6">{agent.desc}</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-semibold" style={{ color: agent.color }}>
                    <span className="flex h-2 w-2 rounded-full animate-pulse" style={{ background: agent.color }} />
                    Active Pipeline Unit
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features List Section ──────────────────────────── */}
        <section id="features" className="w-full flex justify-center py-24 px-6">
          <div className="max-w-6xl w-full">
            <div className="text-center mb-16">
              <h2 className="font-display font-extrabold text-3xl md:text-5xl text-white mb-4">
                Engineered for Fast Launches
              </h2>
              <p className="text-surface-400 text-base md:text-lg max-w-xl mx-auto">
                Production-grade multi-agent orchestration layer, Qdrant memory caches, and Workspace tool integrations.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {FEATURES.map((f, i) => (
                <div key={i} className="p-8 rounded-2xl border border-white/5 bg-[#0d0f22]/50 hover:bg-[#0d0f22]/80 transition-colors">
                  <div className="w-11 h-11 rounded-xl bg-brand-600/15 border border-brand-500/20 flex items-center justify-center mb-6">
                    <f.icon className="w-5 h-5 text-brand-400" />
                  </div>
                  <h3 className="font-display font-bold text-white text-lg mb-2">{f.title}</h3>
                  <p className="text-surface-400 text-sm leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Final Call To Action ───────────────────────────── */}
        <section id="cta" className="w-full flex justify-center py-24 px-6 bg-[#0a0c1a]/60 border-t border-white/5">
          <div className="max-w-4xl w-full p-12 text-center rounded-3xl border border-brand-500/20 bg-gradient-to-b from-[#0f1025] to-[#080914] shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-brand-600/5 to-transparent pointer-events-none" />
            
            <div className="relative z-10 flex flex-col items-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm text-surface-300 mb-6 font-semibold backdrop-blur-md">
                <Check className="w-4 h-4 text-emerald-400" />
                Free to compile. No credit card required.
              </div>

              <h2 className="font-display font-extrabold text-3xl md:text-5xl text-white mb-6">
                Ready to Compile Your <br />
                <span className="gradient-text">Next Launch Campaign?</span>
              </h2>

              <p className="text-surface-400 text-base md:text-lg mb-8 max-w-xl mx-auto leading-relaxed">
                Join hundreds of tech managers and event organizers who have cut down their preparation times from weeks to minutes.
              </p>

              <Link href="/register" className="inline-flex items-center gap-3 bg-gradient-brand text-white px-10 py-4 rounded-xl text-lg font-bold btn-lift shadow-glow-brand group">
                Launch System Free
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>
        </section>

      </main>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="relative z-50 border-t border-white/5 px-6 md:px-12 py-8 bg-[#070812]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-surface-500 font-medium">
          <div className="flex items-center gap-2">
            <Rocket className="w-4 h-4 text-brand-500" />
            <span className="font-bold text-surface-400">HackLaunch AI</span>
            <span>— Compiled via Google ADK, Lyzr & Gemini</span>
          </div>
          <span>© 2026 HackLaunch AI. All rights reserved.</span>
        </div>
      </footer>

    </div>
  );
}
