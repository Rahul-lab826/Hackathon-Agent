"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Rocket, Plus, Search, Calendar, Users, Award, Sparkles, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import type { EventSummary } from "@/types";

export default function DashboardHome() {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function fetchEvents() {
      try {
        const { data } = await api.get("/events/");
        // Check if data is an array or paginated object
        if (Array.isArray(data)) {
          setEvents(data);
        } else if (data && Array.isArray(data.items)) {
          setEvents(data.items);
        } else if (data && typeof data === "object") {
          // Fallback if data is wrapped differently
          setEvents(Object.values(data).filter((item: any) => item && typeof item === 'object' && 'id' in item) as EventSummary[]);
        }
      } catch (err) {
        console.error("Failed to load events", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchEvents();
  }, []);

  const filteredEvents = events.filter(e => 
    (e.name || "Untitled Hackathon").toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.theme.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.domain.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Upper Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-3xl text-white">My Hackathons</h1>
          <p className="text-surface-500 mt-1">Manage and generate launch packages for your events</p>
        </div>
        <Link href="/dashboard/new-event"
          className="flex items-center justify-center gap-2 bg-gradient-brand text-white px-5 py-2.5 rounded-xl font-semibold btn-lift shadow-glow-sm self-start">
          <Plus className="w-5 h-5" />
          Create Hackathon
        </Link>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-sm text-surface-500">Total Hackathons</p>
          <p className="font-display font-bold text-3xl text-white mt-1">{events.length}</p>
        </div>
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-sm text-surface-500">Ready to Launch</p>
          <p className="font-display font-bold text-3xl text-white mt-1">
            {events.filter(e => e.status === "complete").length}
          </p>
        </div>
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-sm text-surface-500">In Progress</p>
          <p className="font-display font-bold text-3xl text-white mt-1">
            {events.filter(e => e.status === "generating").length}
          </p>
        </div>
        <div className="glass-card rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accent-500/5 rounded-full blur-xl pointer-events-none" />
          <p className="text-sm text-surface-500">Average GTM Score</p>
          <p className="font-display font-bold text-3xl text-white mt-1">
            {events.filter(e => e.launch_score !== null).length > 0
              ? Math.round(events.reduce((acc, curr) => acc + (curr.launch_score || 0), 0) / events.filter(e => e.launch_score !== null).length)
              : 0}%
          </p>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-600" />
        <input
          type="text"
          placeholder="Search by name, theme, or domain..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-dark-400 border border-white/5 text-white placeholder-surface-600 rounded-xl py-3 pl-10 pr-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
        />
      </div>

      {/* Main Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 className="w-10 h-10 text-brand-400 animate-spin" />
          <p className="text-surface-500">Loading your events...</p>
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="text-center py-20 glass-card rounded-3xl border border-dashed border-white/10 p-12">
          <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/8 flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-8 h-8 text-brand-400" />
          </div>
          <h3 className="font-semibold text-white text-xl mb-2">No hackathons found</h3>
          <p className="text-surface-500 text-sm max-w-sm mx-auto mb-8">
            Create your first hackathon launch package using our 6-agent system.
          </p>
          <Link href="/dashboard/new-event"
            className="inline-flex items-center gap-2 bg-gradient-brand text-white px-6 py-3 rounded-xl font-bold btn-lift shadow-glow-brand">
            <Plus className="w-5 h-5" /> Launch a Hackathon
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEvents.map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="glass-card rounded-2xl p-6 flex flex-col justify-between"
            >
              <div>
                {/* Header info */}
                <div className="flex justify-between items-start gap-4 mb-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                    event.status === "complete"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : event.status === "generating"
                      ? "bg-brand-500/10 text-brand-400 border-brand-500/20 animate-pulse"
                      : event.status === "error"
                      ? "bg-red-500/10 text-red-400 border-red-500/20"
                      : "bg-white/5 text-surface-500 border-white/6"
                  }`}>
                    {event.status === "complete" ? "Complete" : event.status === "generating" ? "Generating..." : event.status === "error" ? "Error" : "Draft"}
                  </span>
                  
                  {event.launch_score !== null && (
                    <div className="flex items-center gap-1 text-brand-300 font-semibold text-sm bg-brand-500/5 px-2.5 py-1 rounded-full border border-brand-500/10">
                      <Award className="w-4 h-4 text-brand-400" />
                      {event.launch_score}% Score
                    </div>
                  )}
                </div>

                <Link href={`/dashboard/event?id=${event.id}`}>
                  <h3 className="font-display font-bold text-xl text-white hover:text-brand-300 transition-colors line-clamp-1">
                    {event.name || "Untitled Hackathon"}
                  </h3>
                </Link>
                <p className="text-surface-500 text-sm mt-1 line-clamp-2">
                  Theme: {event.theme} &bull; Domain: {event.domain}
                </p>

                {/* Details */}
                <div className="grid grid-cols-2 gap-4 mt-6 py-4 border-t border-b border-white/5">
                  <div className="flex items-center gap-2 text-surface-500 text-xs">
                    <Calendar className="w-3.5 h-3.5 text-surface-600" />
                    <span>{event.duration_hours} Hours</span>
                  </div>
                  <div className="flex items-center gap-2 text-surface-500 text-xs">
                    <Users className="w-3.5 h-3.5 text-surface-600" />
                    <span className="capitalize">{event.location_type || "Hybrid"}</span>
                  </div>
                </div>
              </div>

              {/* Bottom Row */}
              <div className="flex items-center justify-between mt-6">
                <span className="text-xs text-surface-600">
                  Created {formatRelativeTime(event.created_at)}
                </span>
                <Link href={`/dashboard/event?id=${event.id}`}
                  className="text-xs text-brand-300 hover:text-brand-200 font-semibold flex items-center gap-1 group">
                  View Launch Hub
                  <Rocket className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
