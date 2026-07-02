"use client";
import { useState, useRef, useEffect } from "react";
import { 
  Send, Bot, User, Sparkles, Database, Brain, Zap, Loader2, AlertCircle 
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  tokensUsed?: number;
  retrievedMemories?: string[];
  isLoading?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I am HackLaunch AI, your agentic event coordinator. Ask me to outline event schedules, draft marketing copies, outline sponsorship benefits, or search through your past organization details.",
    }
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [currentPromptType, setCurrentPromptType] = useState("event_planning");
  const bottomRef = useRef<HTMLDivElement>(null);

  const PROMPT_TYPES = [
    { id: "event_planning", label: "Event Planning" },
    { id: "landing_page", label: "Landing Pages" },
    { id: "marketing", label: "Social Marketing" },
    { id: "email_campaign", label: "Email Campaigns" },
    { id: "sponsorship", label: "Sponsorship Packages" },
    { id: "budget", label: "Budget Planner" },
  ];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isSending) return;

    const userMessage: Message = {
      id: Math.random().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsSending(true);

    const assistantMessageId = Math.random().toString();
    const loadingMessage: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      isLoading: true,
    };

    setMessages((prev) => [...prev, loadingMessage]);

    try {
      // Connect to Gemini Service Endpoint
      const response = await api.post("/gemini/generate", {
        prompt_type: currentPromptType,
        custom_instructions: userMessage.content,
      });

      const { output, metrics, retrieved_memories } = response.data;
      
      // Format structured output to readable text if object
      let outputText = "";
      if (typeof output === "object" && output !== null) {
        outputText = JSON.stringify(output, null, 2);
      } else {
        outputText = String(output);
      }

      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === assistantMessageId 
            ? {
                ...msg,
                content: outputText,
                isLoading: false,
                tokensUsed: metrics?.total_tokens ?? 0,
                retrievedMemories: retrieved_memories ?? ["No previous events matched current context."]
              }
            : msg
        )
      );
      toast.success("AI Generation completed successfully!");
    } catch (err: any) {
      console.error(err);
      const errorMsg = err.response?.data?.detail ?? "Failed to fetch response from Gemini. Please check API settings.";
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === assistantMessageId 
            ? {
                ...msg,
                content: `Error: ${errorMsg}`,
                isLoading: false,
              }
            : msg
        )
      );
      toast.error("Generation failed. Retry limit hit or rate limits exceeded.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-5xl mx-auto space-y-6">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-4 border-b border-white/5">
        <div>
          <h1 className="font-display font-bold text-3xl text-white">AI Assistant</h1>
          <p className="text-sm text-surface-500 mt-1">Chat directly with Gemini Pro and explore context retrievals</p>
        </div>
        
        {/* Prompt type select pills */}
        <div className="flex flex-wrap gap-2">
          {PROMPT_TYPES.map((t) => (
            <button
              key={t.id}
              onClick={() => setCurrentPromptType(t.id)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all",
                currentPromptType === t.id
                  ? "bg-brand-500/10 border-brand-500 text-brand-300"
                  : "bg-white/3 border-white/5 text-surface-500 hover:text-surface-300"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto glass-card rounded-3xl p-6 space-y-4 min-h-[300px]">
        {messages.map((msg) => {
          const isAssistant = msg.role === "assistant";
          return (
            <div
              key={msg.id}
              className={cn(
                "flex gap-4 max-w-3xl",
                isAssistant ? "mr-auto" : "ml-auto flex-row-reverse"
              )}
            >
              {/* Avatar */}
              <div className={cn(
                "w-9 h-9 rounded-xl flex items-center justify-center border flex-shrink-0",
                isAssistant 
                  ? "bg-brand-500/10 border-brand-500/20 text-brand-400" 
                  : "bg-white/5 border-white/8 text-surface-400"
              )}>
                {isAssistant ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
              </div>

              {/* Message box */}
              <div className="space-y-2">
                <div className={cn(
                  "p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap",
                  isAssistant 
                    ? "bg-dark-300 text-surface-200 border border-white/4" 
                    : "bg-brand-600 text-white shadow-glow-sm"
                )}>
                  {msg.isLoading ? (
                    <div className="flex items-center gap-3 py-1.5">
                      <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                      <span className="text-xs text-surface-500 font-medium">Retrieving Qdrant memories & calling Gemini...</span>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>

                {/* Sub info boxes for assistant messages */}
                {isAssistant && !msg.isLoading && (msg.tokensUsed || msg.retrievedMemories) && (
                  <div className="flex flex-col gap-2 p-3 bg-white/2 rounded-xl border border-white/4 text-[10px] text-surface-500">
                    {msg.tokensUsed !== undefined && (
                      <div className="flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-amber-400" />
                        <span>Token Consumption: <strong>{msg.tokensUsed} tokens</strong></span>
                      </div>
                    )}
                    {msg.retrievedMemories && msg.retrievedMemories.length > 0 && (
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 font-bold text-white">
                          <Database className="w-3.5 h-3.5 text-brand-400" />
                          <span>RAG Memory Matches (Qdrant):</span>
                        </div>
                        <ul className="list-disc pl-4 space-y-0.5 font-medium">
                          {msg.retrievedMemories.map((mem, i) => (
                            <li key={i}>{mem}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input box */}
      <form onSubmit={handleSend} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Enter prompt details for ${currentPromptType.replace("_", " ")}...`}
          disabled={isSending}
          className="flex-1 bg-dark-400 border border-white/5 text-white rounded-2xl py-4 px-5 text-sm focus:border-brand-500/60 focus:outline-none transition-colors placeholder-surface-600 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="bg-gradient-brand text-white w-14 rounded-2xl flex items-center justify-center btn-lift shadow-glow-brand disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
}
