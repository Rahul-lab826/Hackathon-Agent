"use client";
import { create } from "zustand";
import type { AgentName, AgentState, AgentStatus, PipelineState } from "@/types";

const AGENT_ORDER: AgentName[] = ["brand", "structure", "content", "marketing", "email", "execution"];

const makeInitialAgents = (): Record<AgentName, AgentState> =>
  Object.fromEntries(
    AGENT_ORDER.map((name) => [
      name,
      { name, status: "idle" as AgentStatus, output: null, duration_ms: null, error: null },
    ])
  ) as Record<AgentName, AgentState>;

interface AgentStore {
  pipeline: PipelineState;
  startPipeline: (generationId: string) => void;
  setAgentRunning: (name: AgentName) => void;
  setAgentDone: (name: AgentName, output: unknown, duration_ms: number) => void;
  setAgentError: (name: AgentName, error: string) => void;
  setScore: (score: number) => void;
  resetPipeline: () => void;
}

const initialPipeline: PipelineState = {
  generation_id: null,
  overall_progress: 0,
  agents: makeInitialAgents(),
  is_complete: false,
  launch_score: null,
};

export const useAgentStore = create<AgentStore>((set, get) => ({
  pipeline: initialPipeline,

  startPipeline: (generationId) =>
    set({
      pipeline: {
        ...initialPipeline,
        generation_id: generationId,
        agents: makeInitialAgents(),
      },
    }),

  setAgentRunning: (name) =>
    set((state) => ({
      pipeline: {
        ...state.pipeline,
        agents: {
          ...state.pipeline.agents,
          [name]: { ...state.pipeline.agents[name], status: "running" as AgentStatus },
        },
      },
    })),

  setAgentDone: (name, output, duration_ms) =>
    set((state) => {
      const agents = {
        ...state.pipeline.agents,
        [name]: { ...state.pipeline.agents[name], status: "done" as AgentStatus, output, duration_ms },
      };
      const doneCount = Object.values(agents).filter((a) => a.status === "done").length;
      const progress = Math.round((doneCount / AGENT_ORDER.length) * 100);
      return {
        pipeline: {
          ...state.pipeline,
          agents,
          overall_progress: progress,
          is_complete: doneCount === AGENT_ORDER.length,
        },
      };
    }),

  setAgentError: (name, error) =>
    set((state) => ({
      pipeline: {
        ...state.pipeline,
        agents: {
          ...state.pipeline.agents,
          [name]: { ...state.pipeline.agents[name], status: "error" as AgentStatus, error },
        },
      },
    })),

  setScore: (score) =>
    set((state) => ({ pipeline: { ...state.pipeline, launch_score: score } })),

  resetPipeline: () => set({ pipeline: initialPipeline }),
}));
