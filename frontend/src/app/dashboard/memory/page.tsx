"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { 
  Database, Search, Plus, Save, Sparkles, HelpCircle, Loader2, Brain, Check 
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Collection {
  name: string;
  description: string;
}

interface MemoryItem {
  id?: string;
  score?: number;
  payload?: any;
  // Fallbacks if shape is flat
  theme?: string;
  name?: string;
  domain?: string;
  prompt?: string;
  response?: string;
  entity_type?: string;
  details?: any;
}

export default function MemoryExplorerPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [activeCollection, setActiveCollection] = useState("events");
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<MemoryItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Custom manual record state
  const [isAdding, setIsAdding] = useState(false);
  const [newKey, setNewKey] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("brand_guidelines");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    async function loadCollections() {
      try {
        const { data } = await api.get("/memory/collections");
        setCollections(data.collections || []);
      } catch (err) {
        console.error("Failed to load collections", err);
      }
    }
    loadCollections();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!searchQuery.trim()) {
      toast.warning("Please enter a semantic query to search.");
      return;
    }

    setIsSearching(true);
    try {
      const response = await api.post("/memory/search", {
        collection_name: activeCollection,
        query: searchQuery,
        limit: 5
      });
      
      // Parse results depending on whether it is vector matched or flat fallback
      const list = response.data.results || [];
      setResults(list);
      
      if (list.length === 0) {
        toast.info("No matching memories found for current query.");
      } else {
        toast.success(`Retrieved ${list.length} semantic memories!`);
      }
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to execute search. Make sure backend is running.");
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newContent.trim()) {
      toast.warning("Key and Content are required.");
      return;
    }

    setIsSaving(true);
    try {
      await api.post("/memory/save", {
        collection_name: activeCollection,
        entity_id: newKey.replace(/\s+/g, "_").toLowerCase(),
        entity_type: newType,
        details: {
          name: newKey,
          description: newContent,
          timestamp: new Date().toISOString()
        }
      });

      toast.success("Memory persisted and indexed in Qdrant successfully!");
      setNewKey("");
      setNewContent("");
      setIsAdding(false);
      
      // Trigger search refresh
      if (searchQuery) {
        handleSearch();
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to persist custom memory.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/5">
        <div>
          <h1 className="font-display font-bold text-3xl text-white">Memory Explorer</h1>
          <p className="text-sm text-surface-500 mt-1">Audit, search, and seed Qdrant vector-indexed items and context guides</p>
        </div>
        
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="flex items-center justify-center gap-2 bg-gradient-brand text-white px-5 py-2.5 rounded-xl font-bold btn-lift shadow-glow-sm self-start"
        >
          <Plus className="w-4 h-4" /> Seed Custom Memory
        </button>
      </div>

      {/* Manual Seed form overlay/section */}
      {isAdding && (
        <form onSubmit={handleAddMemory} className="glass-card rounded-3xl p-6 border border-brand-500/20 space-y-4">
          <h3 className="text-md font-bold text-white flex items-center gap-2">
            <Brain className="w-4 h-4 text-brand-400" />
            Seed Context Memory in '{activeCollection}' Collection
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] text-surface-500 font-bold uppercase tracking-wider mb-1.5">Memory Key / Name</label>
              <input
                type="text"
                placeholder="e.g. Next.js Hackathon Guide"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-2.5 px-4 text-xs focus:border-brand-500/60 focus:outline-none transition-colors"
                required
              />
            </div>
            <div>
              <label className="block text-[10px] text-surface-500 font-bold uppercase tracking-wider mb-1.5">Details Category Type</label>
              <input
                type="text"
                placeholder="e.g. brand_guideline, preference"
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
                className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-2.5 px-4 text-xs focus:border-brand-500/60 focus:outline-none transition-colors"
              />
            </div>
          </div>
          <div>
            <label className="block text-[10px] text-surface-500 font-bold uppercase tracking-wider mb-1.5">Memory Content (Indexable text block)</label>
            <textarea
              rows={3}
              placeholder="Enter context, brand color preferences, or specific instructions that should be semantically recalled during generation..."
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-2.5 px-4 text-xs focus:border-brand-500/60 focus:outline-none transition-colors resize-none"
              required
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-surface-500 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5"
            >
              {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              Save Memory
            </button>
          </div>
        </form>
      )}

      {/* Main interface layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Collections checklist sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <h3 className="text-xs font-bold text-surface-500 uppercase tracking-wider">Collections</h3>
          <div className="space-y-2">
            {collections.map((col) => (
              <button
                key={col.name}
                onClick={() => {
                  setActiveCollection(col.name);
                  setResults([]);
                }}
                className={cn(
                  "w-full text-left p-4 rounded-2xl border transition-all flex flex-col gap-1",
                  activeCollection === col.name
                    ? "bg-brand-500/10 border-brand-500/30 text-brand-300 shadow-glow-sm"
                    : "bg-dark-400 border-white/4 text-surface-500 hover:text-surface-300 hover:bg-white/2"
                )}
              >
                <div className="flex items-center gap-2">
                  <Database className={cn("w-4 h-4", activeCollection === col.name ? "text-brand-400" : "text-surface-600")} />
                  <span className="font-bold text-xs capitalize">{col.name}</span>
                </div>
                <p className="text-[10px] text-surface-600 leading-normal font-medium">{col.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Search and results panel */}
        <div className="lg:col-span-3 space-y-6">
          {/* Query input */}
          <form onSubmit={handleSearch} className="glass-card rounded-3xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Semantic Similarity Search</h3>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-600" />
                <input
                  type="text"
                  placeholder={`Search for content in '${activeCollection}' collection...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-dark-300 border border-white/8 text-white rounded-xl py-3 pl-10 pr-4 text-xs focus:border-brand-500/60 focus:outline-none transition-colors placeholder-surface-600"
                />
              </div>
              <button
                type="submit"
                disabled={isSearching}
                className="bg-gradient-brand text-white px-5 rounded-xl font-bold btn-lift shadow-glow-brand flex items-center justify-center gap-2 text-xs flex-shrink-0"
              >
                {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : "Query vectors"}
              </button>
            </div>
          </form>

          {/* Results grid */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-surface-500 uppercase tracking-wider">Matched Memory Blocks</h3>
            
            {results.length === 0 ? (
              <div className="glass-card rounded-3xl p-12 text-center text-surface-600 text-xs font-medium">
                No matching memory results found. Enter a query above to run cosine search.
              </div>
            ) : (
              <div className="space-y-4">
                {results.map((item, index) => {
                  // Safely dissect different collection output shapes
                  const matchScore = item.score !== undefined ? Math.round(item.score * 100) : null;
                  const payload = item.payload || item;
                  
                  return (
                    <div key={index} className="glass-card rounded-3xl p-6 space-y-4 border border-white/4 relative overflow-hidden">
                      {/* Highlight Score Badge */}
                      {matchScore !== null && (
                        <div className="absolute top-4 right-4 flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/25">
                          <Sparkles className="w-3 h-3" />
                          <span>{matchScore}% Match</span>
                        </div>
                      )}

                      {/* Header metadata */}
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-brand-400" />
                        <span className="text-[10px] text-surface-500 font-bold uppercase tracking-wider">
                          {payload.entity_type || payload.domain || "indexed_node"}
                        </span>
                      </div>

                      {/* Body texts depending on payload shape */}
                      <div className="text-xs space-y-2">
                        {payload.name && (
                          <p className="font-bold text-white text-sm">{payload.name}</p>
                        )}
                        {payload.theme && (
                          <p className="text-surface-500 font-medium">Theme: <span className="text-white font-semibold">{payload.theme}</span></p>
                        )}
                        {payload.description && (
                          <p className="text-surface-400 leading-relaxed whitespace-pre-wrap">{payload.description}</p>
                        )}
                        {payload.prompt && (
                          <div className="space-y-1.5 p-3 bg-white/2 rounded-xl border border-white/5">
                            <p className="text-[10px] text-surface-500 font-bold">Prompt History</p>
                            <p className="text-white font-semibold">{payload.prompt}</p>
                            {payload.response && (
                              <p className="text-surface-500 leading-relaxed mt-1 font-medium">{payload.response}</p>
                            )}
                          </div>
                        )}
                        {payload.details && (
                          <pre className="p-3 bg-white/2 border border-white/5 rounded-xl text-[10px] text-brand-300 overflow-x-auto font-mono">
                            {JSON.stringify(payload.details, null, 2)}
                          </pre>
                        )}
                        {payload.output_package && (
                          <div className="pt-2">
                            <span className="text-[9px] text-surface-500 font-bold uppercase">Included outputs:</span>
                            <div className="flex flex-wrap gap-1.5 mt-1">
                              {Object.keys(payload.output_package).map((k) => (
                                <span key={k} className="bg-white/5 text-white border border-white/8 px-2 py-0.5 rounded text-[10px] capitalize font-semibold">
                                  {k}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
