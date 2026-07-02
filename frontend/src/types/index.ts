// ── Auth API ───────────────────────────────────────────────────
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  username: string | null;
  avatar_url: string | null;
  bio: string | null;
  phone: string | null;
  location: string | null;
  website: string | null;
  plan: "free" | "pro" | "team" | "enterprise";
  auth_provider: "email" | "google";
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

// ── Event / Hackathon ──────────────────────────────────────────
export type AudienceType = "college_students" | "professionals" | "open" | "mixed";
export type LocationType = "offline" | "online" | "hybrid";
export type EventStatus  = "draft" | "generating" | "complete" | "error";

export interface HackathonBrief {
  theme: string;
  domain: string;
  duration_hours: number;
  audience_type: AudienceType;
  expected_participants: number;
  location_type: LocationType;
  location_detail?: string;
  special_requirements?: string;
}

export interface EventSummary {
  id: string;
  name: string | null;
  theme: string;
  domain: string;
  duration_hours: number;
  location_type: LocationType;
  status: EventStatus;
  launch_score: number | null;
  created_at: string;
}

// ── Agent Pipeline ─────────────────────────────────────────────
export type AgentName = "brand" | "structure" | "content" | "marketing" | "email" | "execution";
export type AgentStatus = "idle" | "queued" | "running" | "done" | "error";

export interface AgentState {
  name: AgentName;
  status: AgentStatus;
  output: unknown | null;
  duration_ms: number | null;
  error: string | null;
}

export interface PipelineState {
  generation_id: string | null;
  overall_progress: number;
  agents: Record<AgentName, AgentState>;
  is_complete: boolean;
  launch_score: number | null;
}

// ── Brand Agent ────────────────────────────────────────────────
export interface BrandOutput {
  event_name: string;
  tagline: string;
  tone_adjectives: string[];
  color_primary: string;
  color_secondary: string;
  color_names: string[];
  persona_text: string;
}

// ── Structure Agent ────────────────────────────────────────────
export interface TimelineItem {
  phase: string;
  title: string;
  description: string;
  duration?: string;
}
export interface ScheduleItem {
  time: string;
  activity: string;
  duration_mins: number;
  type: "session" | "break" | "activity" | "ceremony";
}
export interface StructureOutput {
  timeline: { pre_event: TimelineItem[]; event_day: TimelineItem[]; post_event: TimelineItem[] };
  schedule: ScheduleItem[];
  team_roles: { role: string; responsibilities: string[] }[];
  venue_checklist: string[];
  judging_criteria: { name: string; weight: number; description: string }[];
  prize_structure: { position: string; prize: string; details: string }[];
}

// ── SSE Events ─────────────────────────────────────────────────
export interface SSEAgentStart   { agent: AgentName; timestamp: string }
export interface SSEAgentChunk   { agent: AgentName; chunk: string; index: number }
export interface SSEAgentDone    { agent: AgentName; output: unknown; duration_ms: number }
export interface SSEPipelineDone { score: number; event_id: string }
export interface SSEError        { agent: AgentName; error: string }
