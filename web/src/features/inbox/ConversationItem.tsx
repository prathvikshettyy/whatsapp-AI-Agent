import React from "react";
import { User, AlertCircle, Bot, CheckCircle2 } from "lucide-react";
import { Conversation } from "../../api/types";
import { formatRelative, cn } from "../../lib/utils";

interface ConversationItemProps {
  conversation: Conversation;
  isSelected: boolean;
  onSelect: () => void;
}

export const ConversationItem: React.FC<ConversationItemProps> = ({
  conversation,
  isSelected,
  onSelect,
}) => {
  const isHuman = conversation.status === "human";
  const isBot = conversation.status === "bot";

  return (
    <div
      onClick={onSelect}
      className={cn(
        "flex cursor-pointer items-start gap-3 border-b border-border/60 p-3.5 transition-all text-left group select-none",
        isSelected
          ? "bg-accent/80 border-l-4 border-l-primary pl-2.5 shadow-xs"
          : "hover:bg-accent/40"
      )}
    >
      {/* Avatar */}
      <div className="relative mt-0.5 shrink-0">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-tr from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 text-foreground font-semibold text-xs shadow-xs">
          {conversation.name ? conversation.name.slice(0, 2).toUpperCase() : <User className="h-5 w-5" />}
        </div>
        {/* Status indicator pip */}
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-card",
            isHuman && "bg-amber-500 animate-pulse",
            isBot && "bg-emerald-500",
            conversation.status === "closed" && "bg-slate-400"
          )}
        />
      </div>

      {/* Info column */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1 mb-1">
          <h3 className="truncate text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
            {conversation.name || conversation.wa_id_masked}
          </h3>
          <span className="text-[11px] text-muted-foreground whitespace-nowrap">
            {formatRelative(conversation.last_user_msg_at)}
          </span>
        </div>

        <div className="text-[11px] text-muted-foreground font-mono mb-1">
          {conversation.wa_id_masked}
        </div>

        {/* Message preview snippet */}
        <p className="truncate text-xs text-muted-foreground line-clamp-1 leading-snug">
          {conversation.last_message_preview}
        </p>

        {/* Status Pill & Unread badge */}
        <div className="flex items-center justify-between mt-2">
          {isHuman && (
            <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/15 px-2 py-0.5 text-[10px] font-bold text-amber-600 dark:text-amber-400">
              <AlertCircle className="h-3 w-3" /> Needs Human
            </span>
          )}
          {isBot && (
            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
              <Bot className="h-3 w-3" /> Bot
            </span>
          )}
          {conversation.status === "closed" && (
            <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              <CheckCircle2 className="h-3 w-3" /> Closed
            </span>
          )}

          {conversation.unread > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600 text-white font-bold text-[10px] shadow-xs">
              {conversation.unread}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
