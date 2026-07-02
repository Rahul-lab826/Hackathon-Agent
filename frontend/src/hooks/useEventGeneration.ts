"use client";
import { useEffect, useState } from "react";
import { useAgentStore } from "@/store/agentStore";
import { api } from "@/lib/api";
import { toast } from "sonner";
import type { AgentName } from "@/types";

export function useEventGeneration(eventId: string | null) {
  const { pipeline, startPipeline, setAgentRunning, setAgentDone, setAgentError, setScore } = useAgentStore();
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (!eventId) return;

    let eventSource: EventSource | null = null;

    async function checkStatus() {
      try {
        const { data: event } = await api.get(`/events/${eventId}`);
        
        if (event.status === "generating") {
          setIsGenerating(true);
          const genId = event.generation_id || eventId; // Fallback to eventId if no gen_id
          startPipeline(genId);

          const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
          eventSource = new EventSource(`${API_URL}/generation/${genId}/stream`);

          eventSource.addEventListener("agent_start", (e: any) => {
            const data = JSON.parse(e.data);
            setAgentRunning(data.agent as AgentName);
          });

          eventSource.addEventListener("agent_done", (e: any) => {
            const data = JSON.parse(e.data);
            setAgentDone(data.agent as AgentName, data.output, data.duration_ms || 1000);
          });

          eventSource.addEventListener("pipeline_complete", (e: any) => {
            const data = JSON.parse(e.data);
            setScore(data.score || 100);
            setIsGenerating(false);
            toast.success("All GTM Agents completed their tasks! 🎉");
            eventSource?.close();
          });

          eventSource.addEventListener("error", (e: any) => {
            try {
              const data = JSON.parse(e.data);
              setAgentError(data.agent as AgentName, data.error || "Generation error");
            } catch {
              setIsGenerating(false);
              eventSource?.close();
            }
          });
        } else if (event.status === "complete") {
          // Already generated, load outputs directly into state
          startPipeline(event.id);
          setScore(event.launch_score || 85);
          
          // Populate each agent output from the event object
          const agentNames: AgentName[] = ["brand", "structure", "content", "marketing", "email", "execution"];
          agentNames.forEach((name) => {
            const outputKey = `${name}_output`;
            if (event[outputKey] || event.outputs?.[name]) {
              setAgentDone(name, event[outputKey] || event.outputs[name], 1000);
            } else {
              // Fetch individual if not present on main object
              api.get(`/agents/${eventId}/${name}`)
                .then(({ data }) => {
                  setAgentDone(name, data.raw_output || data, 1000);
                })
                .catch(() => {
                  setAgentError(name, "Failed to load agent output.");
                });
            }
          });
        }
      } catch (err) {
        console.error("Error setting up event stream", err);
      }
    }

    checkStatus();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventId]);

  return { pipeline, isGenerating };
}
