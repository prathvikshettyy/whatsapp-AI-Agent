import React, { useState, useEffect } from "react";
import { Search, AlertCircle, Bot, MessageSquareDashed } from "lucide-react";
import { useConversations } from "../../api/conversations";
import { ConversationItem } from "./ConversationItem";
import { Skeleton } from "../../components/Input";
import { useDebounce } from "../../hooks/useDebounce";
import { cn } from "../../lib/utils";

interface ConversationListProps {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export const ConversationList: React.FC<ConversationListProps> = ({ selectedId, onSelect }) => {
  const [filter, setFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const debouncedSearch = useDebounce(searchTerm, 250);

  const { data: conversations, isLoading, isError } = useConversations(filter, debouncedSearch);

  // Keyboard navigation support: 'j' next, 'k' previous, 'Enter' open
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (["input", "textarea"].includes((e.target as HTMLElement).tagName.toLowerCase())) {
        return; // Don't intercept when user is typing in search or composer
      }
      if (!conversations || conversations.length === 0) return;

      const currentIndex = conversations.findIndex((c) => c.id === selectedId);

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        const nextIndex = currentIndex < conversations.length - 1 ? currentIndex + 1 : 0;
        onSelect(conversations[nextIndex].id);
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : conversations.length - 1;
        onSelect(conversations[prevIndex].id);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [conversations, selectedId, onSelect]);

  const tabs = [
    { id: "all", label: "All" },
    { id: "human", label: "Needs Human", icon: AlertCircle, countColor: "text-amber-500" },
    { id: "bot", label: "Bot", icon: Bot },
    { id: "closed", label: "Closed" },
  ];

  return (
    <div className="flex h-full w-full flex-col border-r border-border bg-card">
      {/* Search Header */}
      <div className="p-3 border-b border-border/80">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search conversations by name, phone..."
            className="w-full rounded-xl border border-input bg-muted/40 pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary focus:bg-background transition-colors"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 mt-2.5 overflow-x-auto pb-0.5 no-scrollbar">
          {tabs.map((tab) => {
            const isActive = filter === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium whitespace-nowrap transition-colors select-none",
                  isActive
                    ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                {tab.icon && <tab.icon className="h-3 w-3" />}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Conversations Scroll Area */}
      <div className="flex-1 overflow-y-auto divide-y divide-border/30">
        {isLoading && (
          <div className="p-4 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-10 w-10 rounded-full shrink-0" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-3/4" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="p-6 text-center text-xs text-destructive">
            Failed to load conversations. Check backend connection.
          </div>
        )}

        {!isLoading && conversations && conversations.length === 0 && (
          <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
            <MessageSquareDashed className="h-10 w-10 opacity-40 mb-2 stroke-1" />
            <p className="text-sm font-medium">No conversations found</p>
            <p className="text-xs mt-1">Try clearing filters or search keywords.</p>
          </div>
        )}

        {!isLoading &&
          conversations?.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isSelected={selectedId === conv.id}
              onSelect={() => onSelect(conv.id)}
            />
          ))}
      </div>
    </div>
  );
};
