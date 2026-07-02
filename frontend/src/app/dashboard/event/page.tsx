"use client";
import { useState, useEffect, Suspense } from "react";
import { useEventGeneration } from "@/hooks/useEventGeneration";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { 
  Rocket, Award, Sparkles, CheckCircle2, Loader2, Play, AlertCircle,
  Copy, Check, FileText, Calendar, Mail, FileDown, ExternalLink, HelpCircle, ChevronRight
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

import { useSearchParams } from "next/navigation";

// Tabs definitions
const TABS = [
  { id: "overview", label: "GTM Hub" },
  { id: "brand", label: "Brand guide" },
  { id: "structure", label: "Schedule & Judging" },
  { id: "content", label: "Copy & FAQ" },
  { id: "marketing", label: "Socials" },
  { id: "emails", label: "Emails" },
  { id: "execution", label: "Operations" },
  { id: "exports", label: "Exports" }
];

function EventDashboardContent() {
  const searchParams = useSearchParams();
  const eventId = searchParams.get("id") || "";
  const { pipeline, isGenerating } = useEventGeneration(eventId);
  const [activeTab, setActiveTab] = useState("overview");
  const [eventDetails, setEventDetails] = useState<any>(null);
  const [copiedTextId, setCopiedTextId] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState<string | null>(null);

  useEffect(() => {
    async function loadDetails() {
      try {
        const { data } = await api.get(`/events/${eventId}`);
        setEventDetails(data);
      } catch (err) {
        console.error("Failed to load event details", err);
      }
    }
    loadDetails();
  }, [eventId, isGenerating]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTextId(id);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopiedTextId(null), 2000);
  };

  const handleExport = async (type: "json" | "pdf" | "docs" | "calendar" | "gmail") => {
    setIsExporting(type);
    try {
      if (type === "json") {
        const { data } = await api.get(`/export/${eventId}/json`);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${eventDetails?.name || "hackathon"}-gtm-package.json`;
        a.click();
        toast.success("GTM Package exported as JSON!");
      } else if (type === "pdf") {
        // PDF Export URL
        const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
        window.open(`${API_URL}/export/${eventId}/pdf`, "_blank");
        toast.success("PDF export started in new tab.");
      } else {
        // MCP Integration trigger
        await api.post(`/export/${eventId}/${type}`);
        toast.success(`Successfully pushed to Google ${type === 'calendar' ? 'Calendar' : type === 'gmail' ? 'Gmail Drafts' : 'Docs'}! 🚀`);
      }
    } catch (err) {
      console.error(err);
      toast.error(`Failed to export to ${type}. Please verify integrations.`);
    } finally {
      setIsExporting(null);
    }
  };

  const getAgentStatusIcon = (status: string) => {
    switch (status) {
      case "done":
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-brand-400 animate-spin" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      default:
        return <div className="w-2 h-2 rounded-full bg-white/20" />;
    }
  };

  const brand = pipeline.agents.brand.output as any;
  const structure = pipeline.agents.structure.output as any;
  const content = pipeline.agents.content.output as any;
  const marketing = pipeline.agents.marketing.output as any;
  const emails = pipeline.agents.email.output as any;
  const execution = pipeline.agents.execution.output as any;

  return (
    <div className="space-y-8">
      {/* Launch Hub Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-surface-500 font-semibold uppercase tracking-wider">Launch Hub</span>
            <span className="text-surface-600">&bull;</span>
            <span className="text-xs text-brand-400 font-semibold">{eventDetails?.theme}</span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white">
            {brand?.event_name || eventDetails?.name || "Hackathon Builder"}
          </h1>
          <p className="text-surface-500 mt-1">{brand?.tagline || "Your AI-generated hackathon GTM campaign"}</p>
        </div>

        {/* Dynamic Launch Score */}
        {pipeline.launch_score !== null && (
          <div className="flex items-center gap-4 bg-white/3 border border-white/8 rounded-2xl p-4 self-start">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/25 flex items-center justify-center">
              <Award className="w-6 h-6 text-brand-400" />
            </div>
            <div>
              <p className="text-xs text-surface-500 font-medium">Launch Readiness</p>
              <p className="font-display font-bold text-2xl text-white">{pipeline.launch_score}% Score</p>
            </div>
          </div>
        )}
      </div>

      {/* Tabs Menu */}
      <div className="flex overflow-x-auto gap-2 pb-1 border-b border-white/5 scrollbar-thin">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-5 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all border",
              activeTab === tab.id
                ? "bg-brand-500/10 border-brand-500 text-brand-300 shadow-glow-sm"
                : "bg-transparent border-transparent text-surface-500 hover:text-surface-200"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Tab Content */}
      <div className="min-h-[400px]">
        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Pipelines overview */}
            <div className="lg:col-span-2 space-y-6">
              <div className="glass-card rounded-3xl p-6">
                <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                  <Rocket className="w-5 h-5 text-brand-400" />
                  Agent Workflow Pipeline
                </h3>

                {/* Visual Workflow Flowchart */}
                <div className="relative border-l-2 border-white/5 pl-6 ml-4 space-y-8">
                  {Object.values(pipeline.agents).map((agent, index) => {
                    const statusColors: Record<string, string> = {
                      done: "bg-emerald-500 text-emerald-400 border-emerald-500/20",
                      running: "bg-brand-500 text-brand-400 border-brand-500/20 animate-pulse",
                      error: "bg-red-500 text-red-400 border-red-500/20",
                      idle: "bg-white/10 text-surface-600 border-white/5",
                      queued: "bg-white/10 text-surface-600 border-white/5"
                    };
                    const colorClass = statusColors[agent.status || "idle"] || statusColors.idle;

                    return (
                      <div key={agent.name} className="relative group">
                        {/* Bullet point connector */}
                        <div className={cn(
                          "absolute -left-[35px] top-1.5 w-4 h-4 rounded-full border-4 border-dark-500 flex items-center justify-center transition-all duration-300",
                          agent.status === "done" ? "bg-emerald-400" :
                          agent.status === "running" ? "bg-brand-400 scale-110" :
                          agent.status === "error" ? "bg-red-400" : "bg-white/20"
                        )} />

                        {/* Card */}
                        <div className="glass p-5 rounded-2xl border border-white/4 group-hover:border-white/10 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-white/3 border border-white/6 flex items-center justify-center font-bold text-xs text-brand-300">
                              0{index + 1}
                            </div>
                            <div>
                              <p className="text-sm font-bold text-white capitalize">{agent.name} Agent</p>
                              <p className="text-[10px] text-surface-500 mt-0.5 uppercase tracking-wider font-semibold">
                                {index === 0 && "Intake & Core Brief"}
                                {index === 1 && "Social Announcement Copy"}
                                {index === 2 && "Hero Headlines & Faq"}
                                {index === 3 && "Outreach Emails"}
                                {index === 4 && "Tiers & Pitch Details"}
                                {index === 5 && "Operational Projections"}
                                {index === 6 && "Mitigation & Roadmap"}
                                {index === 7 && "Qdrant Indexing Sync"}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 self-start md:self-auto">
                            <span className="text-[10px] text-surface-600 font-semibold">
                              {agent.status === "done" ? `${((agent.duration_ms || 1200)/1000).toFixed(1)}s elapsed` : ""}
                            </span>
                            <span className={cn(
                              "text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md border",
                              agent.status === "done" && "bg-emerald-500/5 text-emerald-400",
                              agent.status === "running" && "bg-brand-500/5 text-brand-400",
                              agent.status === "error" && "bg-red-500/5 text-red-400",
                              agent.status === "idle" && "bg-white/3 text-surface-600 border-white/5"
                            )}>
                              {agent.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Sidebar quick overview info */}
            <div className="space-y-6">
              <div className="glass-card rounded-3xl p-6">
                <h3 className="text-md font-bold text-white mb-4">Event Intake Brief</h3>
                <div className="space-y-4 text-sm">
                  <div className="flex justify-between py-2 border-b border-white/5">
                    <span className="text-surface-500">Duration</span>
                    <span className="text-white font-semibold">{eventDetails?.duration_hours} Hours</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-white/5">
                    <span className="text-surface-500">Target Audience</span>
                    <span className="text-white font-semibold capitalize">{eventDetails?.audience_type?.replace("_", " ")}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-white/5">
                    <span className="text-surface-500">Logistics</span>
                    <span className="text-white font-semibold capitalize">{eventDetails?.location_type}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-surface-500">Expected Builders</span>
                    <span className="text-white font-semibold">{eventDetails?.expected_participants}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* BRAND TAB */}
        {activeTab === "brand" && (
          <div className="glass-card rounded-3xl p-8 space-y-8">
            {!brand ? (
              <div className="text-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
                <p className="text-surface-500">Brand identity compiling...</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Colors */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-white">Theme Colors</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 glass rounded-2xl border border-white/5 flex flex-col gap-3">
                        <div className="h-16 rounded-xl shadow-inner-glow" style={{ backgroundColor: brand.color_primary || "#3d5eff" }} />
                        <div>
                          <p className="text-xs text-surface-500 font-medium">Primary Accent</p>
                          <p className="text-sm font-bold text-white uppercase">{brand.color_primary || "#3d5eff"}</p>
                        </div>
                      </div>
                      <div className="p-4 glass rounded-2xl border border-white/5 flex flex-col gap-3">
                        <div className="h-16 rounded-xl shadow-inner-glow" style={{ backgroundColor: brand.color_secondary || "#d946ef" }} />
                        <div>
                          <p className="text-xs text-surface-500 font-medium">Secondary Accent</p>
                          <p className="text-sm font-bold text-white uppercase">{brand.color_secondary || "#d946ef"}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Brand Tone */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-white">Brand Tone Guide</h3>
                    <div className="flex flex-wrap gap-2">
                      {(brand.tone_adjectives || ["Bold", "Innovative", "Collaborative"]).map((t: string) => (
                        <span key={t} className="bg-brand-500/10 text-brand-300 border border-brand-500/20 px-4 py-2 rounded-xl text-sm font-semibold capitalize">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-bold text-white">Target Persona Description</h3>
                  <div className="glass p-6 rounded-2xl border border-white/5 text-surface-300 text-sm leading-relaxed">
                    {brand.persona_text}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* STRUCTURE TAB */}
        {activeTab === "structure" && (
          <div className="glass-card rounded-3xl p-8 space-y-8">
            {!structure ? (
              <div className="text-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
                <p className="text-surface-500">Schedules and judging parameters building...</p>
              </div>
            ) : (
              <>
                {/* Timeline */}
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">Timeline Phases</h3>
                  <div className="space-y-4">
                    {Object.entries(structure.timeline || {}).map(([phase, items]: any) => (
                      <div key={phase} className="glass p-5 rounded-2xl border border-white/5">
                        <h4 className="font-bold text-brand-300 capitalize mb-3 text-sm tracking-wider uppercase">{phase.replace("_", " ")}</h4>
                        <div className="space-y-3">
                          {items.map((item: any, idx: number) => (
                            <div key={idx} className="flex gap-3 text-sm">
                              <span className="text-brand-400 font-bold min-w-[50px]">{item.duration || `Milestone ${idx+1}`}</span>
                              <div>
                                <p className="text-white font-semibold">{item.title}</p>
                                <p className="text-surface-500 text-xs mt-0.5">{item.description}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Schedule timetable */}
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">Hour-by-Hour Schedule</h3>
                  <div className="overflow-x-auto rounded-2xl border border-white/5">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="bg-white/3 text-surface-500 font-bold border-b border-white/5">
                          <th className="p-4">Time Slot</th>
                          <th className="p-4">Activity Name</th>
                          <th className="p-4">Duration</th>
                          <th className="p-4">Category</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(structure.schedule || []).map((item: any, idx: number) => (
                          <tr key={idx} className="border-b border-white/4 hover:bg-white/1 transition-all">
                            <td className="p-4 text-white font-semibold">{item.time}</td>
                            <td className="p-4 text-surface-300">{item.activity}</td>
                            <td className="p-4 text-surface-500">{item.duration_mins} Mins</td>
                            <td className="p-4">
                              <span className={cn(
                                "text-xs font-semibold px-2 py-0.5 rounded-full capitalize",
                                item.type === "session" && "bg-blue-500/10 text-blue-400",
                                item.type === "break" && "bg-amber-500/10 text-amber-400",
                                item.type === "activity" && "bg-purple-500/10 text-purple-400",
                                item.type === "ceremony" && "bg-emerald-500/10 text-emerald-400"
                              )}>
                                {item.type}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Judging Criteria */}
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">Judging Criteria & Weight</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(structure.judging_criteria || []).map((crit: any, idx: number) => (
                      <div key={idx} className="p-5 glass rounded-2xl border border-white/5 flex justify-between items-start gap-4">
                        <div>
                          <h4 className="font-bold text-white text-md mb-1">{crit.name}</h4>
                          <p className="text-xs text-surface-500 leading-relaxed">{crit.description}</p>
                        </div>
                        <span className="bg-brand-500/10 text-brand-300 border border-brand-500/20 px-3 py-1 rounded-xl text-sm font-bold whitespace-nowrap">
                          {crit.weight}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* CONTENT TAB */}
        {activeTab === "content" && (
          <div className="glass-card rounded-3xl p-8 space-y-8">
            {!content ? (
              <div className="text-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
                <p className="text-surface-500">Landing page headlines and FAQs compiling...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Side: Copy Elements */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">Landing Page Content</h3>
                    <p className="text-xs text-surface-500">Copy text blocks generated by the Content Writer agent.</p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-surface-500">Hero Headlines</h4>
                      <button onClick={() => handleCopy(`${content.hero_headline}\n${content.hero_subheadline}`, "hero")}
                        className="text-[10px] text-surface-600 hover:text-white flex items-center gap-1.5 transition-colors">
                        {copiedTextId === "hero" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        Copy Both
                      </button>
                    </div>
                    <div className="glass p-5 rounded-2xl border border-white/5 space-y-2">
                      <p className="text-md font-bold text-white">{content.hero_headline}</p>
                      <p className="text-xs text-surface-500">{content.hero_subheadline}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-surface-500">About Section Copy</h4>
                      <button onClick={() => handleCopy(content.about_copy, "about")}
                        className="text-[10px] text-surface-600 hover:text-white flex items-center gap-1.5 transition-colors">
                        {copiedTextId === "about" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        Copy Copy
                      </button>
                    </div>
                    <div className="glass p-5 rounded-2xl border border-white/5 text-surface-300 text-xs leading-relaxed">
                      {content.about_copy}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-surface-500">Frequently Asked Questions</h4>
                    <div className="space-y-3">
                      {(content.faq || []).slice(0, 3).map((faq: any, idx: number) => (
                        <div key={idx} className="glass p-4 rounded-xl border border-white/5">
                          <p className="font-bold text-white text-xs mb-1">{faq.question}</p>
                          <p className="text-surface-500 text-[10px] leading-relaxed">{faq.answer}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Side: Interactive Browser Live Mockup */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-surface-500">Interactive Mockup Preview</h4>
                  
                  <div className="rounded-2xl border border-white/8 overflow-hidden bg-[#0a0b10] flex flex-col h-[550px] shadow-glow-sm">
                    {/* Simulated Browser Bar */}
                    <div className="bg-[#12131a] px-4 py-3 flex items-center gap-2 border-b border-white/5">
                      <div className="flex gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                      </div>
                      <div className="mx-auto bg-dark-500/60 border border-white/5 rounded-md px-12 py-1 text-[9px] text-surface-600 font-mono select-none">
                        https://{brand?.event_name?.toLowerCase()?.replace(/\s+/g, "-") || "hackathon"}.devpost.com
                      </div>
                    </div>

                    {/* Mockup Canvas */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-thin text-white">
                      {/* Nav Mock */}
                      <header className="flex justify-between items-center pb-4 border-b border-white/5">
                        <span className="font-bold text-sm" style={{ color: brand?.color_primary || "#3d5eff" }}>
                          {brand?.event_name || "Hackathon"}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] text-surface-500 font-medium">Schedule</span>
                          <span className="text-[10px] text-surface-500 font-medium">FAQ</span>
                          <span className="text-[10px] text-white px-3 py-1.5 rounded-lg text-center font-bold text-xs" style={{ backgroundColor: brand?.color_primary || "#3d5eff" }}>
                            Register
                          </span>
                        </div>
                      </header>

                      {/* Hero Section Mock */}
                      <div className="text-center py-10 space-y-4">
                        <h2 className="text-xl font-extrabold tracking-tight leading-tight max-w-md mx-auto">
                          {content.hero_headline}
                        </h2>
                        <p className="text-[10px] text-surface-500 max-w-sm mx-auto leading-normal">
                          {content.hero_subheadline}
                        </p>
                        <div className="pt-2 flex justify-center gap-2.5">
                          <button className="px-4 py-2 rounded-xl text-[10px] font-bold" style={{ backgroundColor: brand?.color_primary || "#3d5eff" }}>
                            Join Hackathon
                          </button>
                          <button className="px-4 py-2 bg-white/5 border border-white/8 hover:bg-white/10 rounded-xl text-[10px] font-bold">
                            View Schedule
                          </button>
                        </div>
                      </div>

                      {/* About Mock */}
                      <div className="space-y-2.5 bg-white/2 border border-white/5 p-4 rounded-xl">
                        <h3 className="text-xs font-bold" style={{ color: brand?.color_secondary || "#d946ef" }}>About the Event</h3>
                        <p className="text-[10px] text-surface-500 leading-relaxed">
                          {content.about_copy}
                        </p>
                      </div>

                      {/* FAQ Mock */}
                      <div className="space-y-3">
                        <h3 className="text-xs font-bold text-center">FAQs</h3>
                        <div className="space-y-2">
                          {(content.faq || []).map((faq: any, i: number) => (
                            <div key={i} className="p-3 bg-[#111218] border border-white/4 rounded-lg space-y-1">
                              <p className="font-bold text-[10px] text-white">{faq.question}</p>
                              <p className="text-[9px] text-surface-500 leading-normal">{faq.answer}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* MARKETING TAB */}
        {activeTab === "marketing" && (
          <div className="glass-card rounded-3xl p-8 space-y-8">
            {!marketing ? (
              <div className="text-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
                <p className="text-surface-500">Social pipelines compiling...</p>
              </div>
            ) : (
              <div className="space-y-8">
                {/* LinkedIn Mockup */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs uppercase tracking-wider text-blue-400">LinkedIn Preview</span>
                    <button onClick={() => handleCopy(marketing.linkedin_announcement, "li")}
                      className="text-xs text-surface-500 hover:text-white flex items-center gap-1.5 transition-colors">
                      {copiedTextId === "li" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Post Text
                    </button>
                  </div>

                  <div className="bg-[#18191d] rounded-2xl border border-white/5 p-5 max-w-2xl space-y-4">
                    {/* Header */}
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-brand-500/10 border border-brand-500/25 flex items-center justify-center text-xs font-bold text-brand-400 uppercase">
                        EP
                      </div>
                      <div>
                        <p className="text-xs font-bold text-white flex items-center gap-1.5">
                          Event Producer <span className="text-[10px] text-surface-600 font-medium">• 1st</span>
                        </p>
                        <p className="text-[9px] text-surface-600">Event Management & Promotion</p>
                        <p className="text-[9px] text-surface-600">Just now</p>
                      </div>
                    </div>
                    {/* Content */}
                    <p className="text-xs text-surface-300 whitespace-pre-wrap leading-relaxed">
                      {marketing.linkedin_announcement}
                    </p>
                    {/* Interaction Bar */}
                    <div className="h-px bg-white/5" />
                    <div className="flex justify-between text-[10px] text-surface-500 px-2 font-semibold">
                      <span>👍 Like</span>
                      <span>💬 Comment</span>
                      <span>🔄 Share</span>
                      <span>📤 Send</span>
                    </div>
                  </div>
                </div>

                {/* Twitter Mockup */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs uppercase tracking-wider text-sky-400">Twitter Thread Preview</span>
                    <button onClick={() => handleCopy((marketing.twitter_thread || []).map((t: any) => t.content).join("\n\n---\n\n"), "twt")}
                      className="text-xs text-surface-500 hover:text-white flex items-center gap-1.5 transition-colors">
                      {copiedTextId === "twt" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Thread Text
                    </button>
                  </div>

                  <div className="space-y-3 max-w-2xl">
                    {(marketing.twitter_thread || []).map((tweet: any, idx: number) => (
                      <div key={idx} className="bg-[#15181c] rounded-2xl border border-white/5 p-4 space-y-3 relative">
                        {/* Connecting Line between tweets in a thread */}
                        {idx < (marketing.twitter_thread.length - 1) && (
                          <div className="absolute left-[30px] top-[50px] bottom-[-20px] w-0.5 bg-white/5 z-0" />
                        )}

                        <div className="flex gap-3 relative z-10">
                          {/* Avatar */}
                          <div className="w-9 h-9 rounded-full bg-sky-500/10 border border-sky-500/25 flex items-center justify-center text-xs font-bold text-sky-400 flex-shrink-0">
                            H
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-1.5">
                              <span className="text-xs font-bold text-white">HackLaunch Host</span>
                              <span className="text-[10px] text-surface-600">@hacklaunch_dev • {idx + 1}/{marketing.twitter_thread.length}</span>
                            </div>
                            <p className="text-xs text-surface-300 leading-normal whitespace-pre-wrap">
                              {tweet.content}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* EMAILS TAB */}
        {activeTab === "emails" && (
          <div className="glass-card rounded-3xl p-8 space-y-8">
            {!emails ? (
              <div className="text-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
                <p className="text-surface-500">Email campaigns preparing...</p>
              </div>
            ) : (
              <div className="space-y-8 max-w-4xl">
                {/* Invite Email */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs uppercase tracking-wider text-brand-300">Builder Invitation Email</span>
                    <button onClick={() => handleCopy(`Subject: ${emails.invite_subject}\n\n${emails.invite_body}`, "invite_mail")}
                      className="text-xs text-surface-500 hover:text-white flex items-center gap-1.5 transition-colors">
                      {copiedTextId === "invite_mail" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Subject + Body
                    </button>
                  </div>

                  {/* Mailbox Container */}
                  <div className="rounded-2xl border border-white/5 bg-[#0f1015] overflow-hidden shadow-glow-sm">
                    {/* Header */}
                    <div className="bg-[#16171d] px-5 py-4 border-b border-white/5 space-y-2 text-xs">
                      <div className="flex justify-between text-surface-500">
                        <span>To: <strong className="text-white font-medium">[Builder Candidates List]</strong></span>
                        <span>contact@hacklaunch.ai</span>
                      </div>
                      <div className="flex justify-between text-surface-500">
                        <span>Subject: <strong className="text-brand-300 font-bold">{emails.invite_subject}</strong></span>
                        <span>Just now</span>
                      </div>
                    </div>
                    {/* Mail Body */}
                    <div className="p-6 text-surface-300 text-xs leading-relaxed whitespace-pre-wrap font-sans bg-[#0c0d12]">
                      {emails.invite_body}
                    </div>
                  </div>
                </div>

                {/* Sponsor Email */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs uppercase tracking-wider text-brand-300">Sponsor Outreach Email</span>
                    <button onClick={() => handleCopy(`Subject: ${emails.sponsor_subject}\n\n${emails.sponsor_body}`, "sponsor_mail")}
                      className="text-xs text-surface-500 hover:text-white flex items-center gap-1.5 transition-colors">
                      {copiedTextId === "sponsor_mail" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy Subject + Body
                    </button>
                  </div>

                  {/* Mailbox Container */}
                  <div className="rounded-2xl border border-white/5 bg-[#0f1015] overflow-hidden shadow-glow-sm">
                    {/* Header */}
                    <div className="bg-[#16171d] px-5 py-4 border-b border-white/5 space-y-2 text-xs">
                      <div className="flex justify-between text-surface-500">
                        <span>To: <strong className="text-white font-medium">[Sponsor Outreach Partners]</strong></span>
                        <span>sponsors@hacklaunch.ai</span>
                      </div>
                      <div className="flex justify-between text-surface-500">
                        <span>Subject: <strong className="text-brand-300 font-bold">{emails.sponsor_subject}</strong></span>
                        <span>Just now</span>
                      </div>
                    </div>
                    {/* Mail Body */}
                    <div className="p-6 text-surface-300 text-xs leading-relaxed whitespace-pre-wrap font-sans bg-[#0c0d12]">
                      {emails.sponsor_body}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* OPERATIONS TAB */}
        {activeTab === "execution" && (
          <div className="glass-card rounded-3xl p-8 space-y-8">
            {!execution ? (
              <div className="text-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
                <p className="text-surface-500">Execution templates compiling...</p>
              </div>
            ) : (
              <>
                {/* Weekly Plan */}
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">Execution Plan (Week-by-Week)</h3>
                  <div className="space-y-4">
                    {(execution.weekly_plan || []).map((week: any, idx: number) => (
                      <div key={idx} className="glass p-5 rounded-2xl border border-white/5">
                        <h4 className="font-bold text-brand-300 mb-3 text-sm">Week {week.week}</h4>
                        <ul className="space-y-2">
                          {(week.tasks || []).map((task: string, tIdx: number) => (
                            <li key={tIdx} className="flex gap-2 text-xs text-surface-300">
                              <span className="text-brand-400 font-semibold">•</span>
                              <span>{task}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Risk Mitigation */}
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-white">Risk Mitigation Plan</h3>
                  <div className="space-y-3">
                    {(execution.risk_plan || []).map((risk: any, idx: number) => (
                      <div key={idx} className="p-4 glass rounded-xl border border-white/5 space-y-1">
                        <p className="font-bold text-white text-sm flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-red-400" />
                          {risk.risk}
                        </p>
                        <p className="text-surface-500 text-xs pl-4">{risk.mitigation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* EXPORTS TAB */}
        {activeTab === "exports" && (
          <div className="glass-card rounded-3xl p-8 space-y-6">
            <div>
              <h3 className="text-xl font-bold text-white">Export & Integration Hub</h3>
              <p className="text-sm text-surface-500 mt-1">Download raw GTM assets or sync them directly into your Google Workspace toolchain.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* File Exports */}
              <div className="glass p-6 rounded-2xl border border-white/5 space-y-4">
                <h4 className="font-semibold text-white text-sm flex items-center gap-2">
                  <FileDown className="w-4 h-4 text-brand-400" />
                  Asset Downloads
                </h4>
                <div className="space-y-2">
                  <button
                    disabled={isExporting !== null}
                    onClick={() => handleExport("json")}
                    className="w-full bg-white/5 hover:bg-white/10 text-white py-3 px-4 rounded-xl text-xs font-bold border border-white/6 transition-all flex items-center justify-between"
                  >
                    <span>Download GTM JSON Package</span>
                    {isExporting === "json" ? <Loader2 className="w-4 h-4 animate-spin text-brand-400" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  <button
                    disabled={isExporting !== null}
                    onClick={() => handleExport("pdf")}
                    className="w-full bg-white/5 hover:bg-white/10 text-white py-3 px-4 rounded-xl text-xs font-bold border border-white/6 transition-all flex items-center justify-between"
                  >
                    <span>Export Complete GTM PDF Book</span>
                    {isExporting === "pdf" ? <Loader2 className="w-4 h-4 animate-spin text-brand-400" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* MCP Syncs */}
              <div className="glass p-6 rounded-2xl border border-white/5 space-y-4">
                <h4 className="font-semibold text-white text-sm flex items-center gap-2">
                  <ExternalLink className="w-4 h-4 text-brand-400" />
                  Google Integration Actions
                </h4>
                <div className="space-y-2">
                  <button
                    disabled={isExporting !== null}
                    onClick={() => handleExport("docs")}
                    className="w-full bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 py-3 px-4 rounded-xl text-xs font-bold border border-brand-500/20 transition-all flex items-center justify-between"
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="w-4 h-4" /> Sync to Google Docs
                    </span>
                    {isExporting === "docs" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
                  </button>

                  <button
                    disabled={isExporting !== null}
                    onClick={() => handleExport("calendar")}
                    className="w-full bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 py-3 px-4 rounded-xl text-xs font-bold border border-brand-500/20 transition-all flex items-center justify-between"
                  >
                    <span className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" /> Create Google Calendar Milestones
                    </span>
                    {isExporting === "calendar" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
                  </button>

                  <button
                    disabled={isExporting !== null}
                    onClick={() => handleExport("gmail")}
                    className="w-full bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 py-3 px-4 rounded-xl text-xs font-bold border border-brand-500/20 transition-all flex items-center justify-between"
                  >
                    <span className="flex items-center gap-2">
                      <Mail className="w-4 h-4" /> Draft emails in Gmail
                    </span>
                    {isExporting === "gmail" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function EventDashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-screen text-white gap-4 bg-[#0a0a0c]">
        <Loader2 className="w-10 h-10 animate-spin text-brand-400" />
        <span className="font-semibold text-lg text-surface-300">Loading GTM Launch Hub...</span>
      </div>
    }>
      <EventDashboardContent />
    </Suspense>
  );
}
