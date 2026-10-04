import React, { useState } from "react";
import { Bot, User as UserIcon, CheckCheck, Clock, AlertCircle, ChevronDown, ChevronRight, Wrench, ShieldAlert } from "lucide-react";
import { Message } from "../../api/types";
import { formatTime, cn } from "../../lib/utils";

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [expandedTool, setExpandedTool] = useState<number | null>(null);

  const isUser = message.role === "user";
  const isBot = message.role === "bot";
  const isStaff = message.role === "staff";

  return (
    <div
      className={cn(
        "flex w-full gap-2.5 my-2.5 animate-in fade-in-50 duration-200",
        isStaff ? "justify-end" : "justify-start"
      )}
    >
      {/* Bot / User Avatar */}
      {!isStaff && (
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold mt-1 shadow-xs",
            isUser ? "bg-muted text-foreground" : "bg-emerald-600 text-white"
          )}
        >
          {isUser ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>
      )}

      {/* Bubble Container */}
      <div className={cn("flex flex-col max-w-[80%] md:max-w-[70%]", isStaff && "items-end")}>
        {/* Role label header */}
        <div className="flex items-center gap-1.5 px-1 mb-1 text-[11px] text-muted-foreground font-medium">
          {isUser && <span>WhatsApp User</span>}
          {isBot && (
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <Bot className="h-3 w-3" /> Claude Assistant
            </span>
          )}
          {isStaff && <span className="text-primary font-semibold">Staff Agent</span>}
          <span>•</span>
          <span>{formatTime(message.created_at)}</span>
        </div>

        {/* Bubble Body */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm shadow-xs transition-colors whitespace-pre-wrap break-words",
            isUser && "rounded-tl-xs bg-card border border-border text-card-foreground",
            isBot && "rounded-tl-xs bg-emerald-50/70 border border-emerald-500/20 text-emerald-950 dark:bg-emerald-950/30 dark:border-emerald-500/30 dark:text-emerald-100",
            isStaff && "rounded-tr-xs bg-primary text-primary-foreground font-normal"
          )}
        >
          {/* Media preview (if attached) */}
          {message.media && (
            <div className="mb-2 overflow-hidden rounded-lg border border-black/10">
              {message.media.type === "image" && (
                <img
                  src={message.media.url}
                  alt="Attachment"
                  className="max-h-60 w-full object-cover"
                />
              )}
              {message.media.type === "audio" && (
                <div className="p-2 bg-black/5 dark:bg-white/5 rounded">
                  <audio controls className="h-8 w-full">
                    <source src={message.media.url} />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
            </div>
          )}

          {/* Text Content */}
          <div className="leading-relaxed">{message.content}</div>

          {/* Expandable Tool Call Chips */}
          {message.tool_calls && message.tool_calls.length > 0 && (
            <div className="mt-2.5 pt-2 border-t border-emerald-500/20 space-y-1.5">
              <div className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                <Wrench className="h-3 w-3" /> Tools Executed ({message.tool_calls.length})
              </div>

              {message.tool_calls.map((tool, idx) => {
                const isExpanded = expandedTool === idx;
                const requiresConf = tool.status === "requires_user_confirmation";
                const isErr = tool.status === "error";

                return (
                  <div
                    key={idx}
                    className="rounded-lg border border-black/10 dark:border-white/10 bg-black/5 dark:bg-white/5 text-xs overflow-hidden"
                  >
                    <button
                      onClick={() => setExpandedTool(isExpanded ? null : idx)}
                      className="flex w-full items-center justify-between p-2 text-left hover:bg-black/5 transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 opacity-60" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 opacity-60" />
                        )}
                        <span className="font-mono font-medium">{tool.name}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        {requiresConf && (
                          <span className="flex items-center gap-1 rounded bg-amber-500/20 text-amber-700 dark:text-amber-400 px-1.5 py-0.5 text-[10px] font-semibold">
                            <ShieldAlert className="h-3 w-3" /> Needs Confirmation
                          </span>
                        )}
                        {isErr && (
                          <span className="rounded bg-destructive/20 text-destructive px-1.5 py-0.5 text-[10px] font-semibold">
                            Failed
                          </span>
                        )}
                        {!requiresConf && !isErr && (
                          <span className="rounded bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 px-1.5 py-0.5 text-[10px] font-semibold">
                            OK
                          </span>
                        )}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="p-2.5 border-t border-black/5 dark:border-white/5 bg-black/10 dark:bg-black/40 font-mono text-[11px] space-y-1.5 overflow-x-auto">
                        {tool.args && (
                          <div>
                            <span className="font-semibold text-muted-foreground">Arguments:</span>
                            <pre className="mt-0.5 p-1 rounded bg-background/50 overflow-x-auto">
                              {JSON.stringify(tool.args, null, 2)}
                            </pre>
                          </div>
                        )}
                        {tool.result && (
                          <div>
                            <span className="font-semibold text-muted-foreground">Result:</span>
                            <pre className="mt-0.5 p-1 rounded bg-background/50 overflow-x-auto">
                              {JSON.stringify(tool.result, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Message Delivery Status for Staff */}
        {isStaff && (
          <div className="flex items-center gap-1 px-1 mt-1 text-[11px] text-muted-foreground">
            {message.pending ? (
              <span className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-3 w-3 animate-spin" /> Sending...
              </span>
            ) : message.failed ? (
              <span className="flex items-center gap-1 text-destructive font-medium">
                <AlertCircle className="h-3 w-3" /> Delivery Failed
              </span>
            ) : (
              <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                <CheckCheck className="h-3.5 w-3.5" /> Sent to WhatsApp
              </span>
            )}
          </div>
        )}
      </div>

      {/* Staff Avatar */}
      {isStaff && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold mt-1 shadow-xs">
          ST
        </div>
      )}
    </div>
  );
};
