"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { 
  Rocket, Sparkles, ChevronLeft, ChevronRight, Check,
  Clock, Users, MapPin, AlertCircle, Info, Award
} from "lucide-react";
import { hackathonBriefSchema, type HackathonBriefData } from "@/lib/validators";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const STEPS = [
  { id: 1, title: "Theme & Domain", desc: "What's the core focus?" },
  { id: 2, title: "Duration & Scope", desc: "How long and who for?" },
  { id: 3, title: "Logistics", desc: "Where will it happen?" },
  { id: 4, title: "Refinements", desc: "Special requirements?" }
];

export default function NewEventPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitCooldown, setSubmitCooldown] = useState(true);

  useEffect(() => {
    if (currentStep === 4) {
      const timer = setTimeout(() => setSubmitCooldown(false), 800);
      return () => clearTimeout(timer);
    } else {
      setSubmitCooldown(true);
    }
  }, [currentStep]);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<HackathonBriefData>({
    resolver: zodResolver(hackathonBriefSchema),
    defaultValues: {
      theme: "",
      domain: "",
      duration_hours: 36,
      audience_type: "college_students",
      expected_participants: 100,
      location_type: "offline",
      location_detail: "",
      special_requirements: ""
    }
  });

  const nextStep = () => {
    // Basic validation check per step if necessary
    if (currentStep === 1) {
      if (!watch("theme") || !watch("domain")) {
        toast.error("Please enter a Theme and a Domain first.");
        return;
      }
    }
    if (currentStep < 4) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const onSubmit = async (data: HackathonBriefData) => {
    if (currentStep < 4) {
      nextStep();
      return;
    }
    setIsSubmitting(true);
    try {
      // 1. Create the event
      const response = await api.post("/events/", data);
      const eventId = response.data.id;

      
      // 2. Trigger generation
      await api.post("/generation/start", { event_id: eventId });

      toast.success("Hackathon GTM setup initialized successfully! 🚀");
      // 3. Direct to launch hub
      router.push(`/dashboard/event?id=${eventId}`);
    } catch (err) {
      console.error(err);
      toast.error("Failed to start hackathon generation. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const watchDuration = watch("duration_hours");
  const watchAudience = watch("audience_type");
  const watchLocationType = watch("location_type");

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Upper header */}
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()}
          className="w-10 h-10 glass rounded-xl flex items-center justify-center text-surface-500 hover:text-white transition-colors">
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="font-display font-bold text-3xl text-white">Setup Hackathon</h1>
          <p className="text-surface-500 mt-1">Answer a few questions to activate the 6 GTM agents</p>
        </div>
      </div>

      {/* Steps Indicator */}
      <div className="grid grid-cols-4 gap-2">
        {STEPS.map((s) => (
          <div key={s.id} className="space-y-2">
            <div className={cn(
              "h-1.5 rounded-full transition-all duration-300",
              currentStep >= s.id ? "bg-gradient-brand shadow-glow-sm" : "bg-white/5"
            )} />
            <div className="hidden sm:block">
              <p className={cn(
                "text-xs font-semibold",
                currentStep === s.id ? "text-brand-300" : "text-surface-500"
              )}>{s.title}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Form Content */}
      <form 
        onSubmit={handleSubmit(onSubmit)} 
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT") {
            e.preventDefault();
          }
        }}
        className="glass-card rounded-3xl p-8 relative overflow-hidden space-y-6"
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 rounded-full blur-3xl pointer-events-none" />


        <AnimatePresence mode="wait">
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="space-y-6"
            >
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Theme & Domain</h3>
                <p className="text-sm text-surface-500">Provide the core focus area of your hackathon.</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-surface-300 mb-1.5 font-medium">Theme Name / Concept</label>
                  <input
                    {...register("theme")}
                    placeholder="e.g. GenAI Agents, Decarbonization, DeFi Innovation..."
                    className="w-full bg-dark-300 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                  <p className="text-xs text-surface-600 mt-1">Specify a unique focus or tagline style theme.</p>
                </div>

                <div>
                  <label className="block text-sm text-surface-300 mb-1.5 font-medium">Domain Area</label>
                  <input
                    {...register("domain")}
                    placeholder="e.g. Artificial Intelligence, Sustainability, FinTech..."
                    className="w-full bg-dark-300 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="space-y-6"
            >
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Duration & Scope</h3>
                <p className="text-sm text-surface-500">Decide how long your event will run and who it is tailored for.</p>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm text-surface-300 mb-3 font-medium">Duration (Hours)</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[24, 36, 48].map((hours) => (
                      <button
                        key={hours}
                        type="button"
                        onClick={() => setValue("duration_hours", hours)}
                        className={cn(
                          "py-3.5 px-4 rounded-xl border font-semibold text-sm transition-all flex flex-col items-center justify-center gap-1",
                          watchDuration === hours
                            ? "bg-brand-500/10 border-brand-500 text-brand-300 shadow-glow-sm"
                            : "bg-dark-300 border-white/8 text-surface-400 hover:border-white/20 hover:text-white"
                        )}
                      >
                        <Clock className="w-4 h-4" />
                        <span>{hours} Hours</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-surface-300 mb-3 font-medium">Target Audience</label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: "college_students", label: "Students Only" },
                      { key: "professionals", label: "Professionals Only" },
                      { key: "open", label: "Open to All" },
                      { key: "mixed", label: "Mixed / Enterprise" }
                    ].map((opt) => (
                      <button
                        key={opt.key}
                        type="button"
                        onClick={() => setValue("audience_type", opt.key as any)}
                        className={cn(
                          "py-3 px-4 rounded-xl border text-sm font-semibold transition-all text-left",
                          watchAudience === opt.key
                            ? "bg-brand-500/10 border-brand-500 text-brand-300 shadow-glow-sm"
                            : "bg-dark-300 border-white/8 text-surface-400 hover:border-white/20 hover:text-white"
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {currentStep === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="space-y-6"
            >
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Logistics</h3>
                <p className="text-sm text-surface-500">Where are participants building?</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-surface-300 mb-3 font-medium">Location Type</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { key: "offline", label: "In-Person" },
                      { key: "online", label: "Virtual" },
                      { key: "hybrid", label: "Hybrid" }
                    ].map((opt) => (
                      <button
                        key={opt.key}
                        type="button"
                        onClick={() => setValue("location_type", opt.key as any)}
                        className={cn(
                          "py-3.5 px-4 rounded-xl border font-semibold text-sm transition-all flex flex-col items-center justify-center gap-1",
                          watchLocationType === opt.key
                            ? "bg-brand-500/10 border-brand-500 text-brand-300 shadow-glow-sm"
                            : "bg-dark-300 border-white/8 text-surface-400 hover:border-white/20 hover:text-white"
                        )}
                      >
                        <MapPin className="w-4 h-4" />
                        <span>{opt.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-surface-300 mb-1.5 font-medium">Location Details / Platforms</label>
                  <input
                    {...register("location_detail")}
                    placeholder="e.g. Bangalore Campus, Discord & Devpost, Hybrid (SF & Virtual)..."
                    className="w-full bg-dark-300 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm text-surface-300 mb-1.5 font-medium">Expected Participants Size</label>
                  <input
                    type="number"
                    {...register("expected_participants", { valueAsNumber: true })}
                    placeholder="100"
                    className="w-full bg-dark-300 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {currentStep === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="space-y-6"
            >
              <div>
                <h3 className="text-xl font-bold text-white mb-2">Special Requirements & Refinements</h3>
                <p className="text-sm text-surface-500">Provide any specific guidelines, sponsors, or prize details to incorporate.</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-surface-300 mb-1.5 font-medium">Instructions & Sponsors (Optional)</label>
                  <textarea
                    {...register("special_requirements")}
                    rows={4}
                    placeholder="e.g. Sponsors: Google Cloud, Lyzr. Focus heavily on beginner developers. Prizes must fit in a total pool of $10,000. Include mentorship sessions in schedule."
                    className="w-full bg-dark-300 border border-white/8 text-white placeholder-surface-600 rounded-xl py-3 px-4 text-sm focus:border-brand-500/60 focus:outline-none transition-colors resize-none"
                  />
                </div>

                <div className="glass p-4 rounded-xl flex gap-3 text-xs text-surface-400">
                  <Info className="w-4 h-4 text-brand-400 flex-shrink-0" />
                  <p>
                    By clicking &quot;Activate Agents&quot;, our system will spin up 6 specialized agents in the background to build your brand guide, timeline, schedule, landing page copywriting, social pipeline, email triggers, and operational checklists.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-white/5">
          <button
            type="button"
            onClick={prevStep}
            className={cn(
              "px-5 py-2.5 rounded-xl border border-white/5 text-sm font-semibold hover:bg-white/5 transition-all text-surface-300 flex items-center gap-1.5",
              currentStep === 1 ? "opacity-0 pointer-events-none" : ""
            )}
          >
            <ChevronLeft className="w-4 h-4" /> Back
          </button>

          {currentStep < 4 ? (
            <button
              type="button"
              onClick={nextStep}
              className="bg-gradient-brand text-white px-6 py-3 rounded-xl font-semibold btn-lift shadow-glow-sm flex items-center gap-1.5"
            >
              Continue <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting || submitCooldown}
              className="bg-gradient-brand text-white px-8 py-3.5 rounded-xl font-bold btn-lift shadow-glow-brand flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="w-4 h-4" />
              {isSubmitting ? "Activating Agents..." : submitCooldown ? "Loading Step 4..." : "Activate Agents ✨"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
