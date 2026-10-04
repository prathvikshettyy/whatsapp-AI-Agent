import React, { useState } from "react";
import { MessageSquare, ShieldCheck, Zap } from "lucide-react";
import { useConversations } from "../../api/conversations";
import { ConversationList } from "./ConversationList";
import { Thread } from "./Thread";

export const InboxPage: React.FC = () => {
  const { data: conversations } = useConversations();
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    return conversations && conversations.length > 0 ? conversations[0].id : null;
  });

  // Default to first conversation if none selected
  const activeId = selectedId || (conversations && conversations.length > 0 ? conversations[0].id : null);
  const activeConversation = conversations?.find((c) => c.id === activeId);

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Conversation List Panel */}
      <div
        className={`w-full md:w-[380px] lg:w-[420px] shrink-0 h-full ${
          activeConversation ? "hidden md:block" : "block"
        }`}
      >
        <ConversationList selectedId={activeId} onSelect={(id) => setSelectedId(id)} />
      </div>

      {/* Conversation Thread / Detail Panel */}
      <div
        className={`flex-1 h-full min-w-0 ${
          activeConversation ? "block" : "hidden md:flex"
        }`}
      >
        {activeConversation ? (
          <Thread
            conversation={activeConversation}
            onBack={() => setSelectedId(null)}
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center p-8 text-center bg-muted/10">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary mb-4 shadow-sm">
              <MessageSquare className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold">Select a conversation</h3>
            <p className="text-sm text-muted-foreground max-w-sm mt-1">
              Choose a contact from the inbox list to inspect their message history, view tool executions, or take over from the bot.
            </p>

            <div className="grid grid-cols-2 gap-3 mt-8 max-w-md w-full text-left">
              <div className="rounded-xl border border-border bg-card p-3 shadow-xs">
                <div className="flex items-center gap-2 font-semibold text-xs text-foreground mb-1">
                  <ShieldCheck className="h-4 w-4 text-emerald-500" /> Human Takeover
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Pause bot automation and respond manually whenever a customer asks for a human.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-3 shadow-xs">
                <div className="flex items-center gap-2 font-semibold text-xs text-foreground mb-1">
                  <Zap className="h-4 w-4 text-amber-500" /> 24h Window
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Real-time countdown keeping staff compliant with Meta Business Messaging policies.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
