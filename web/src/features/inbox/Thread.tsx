import React, { useEffect, useRef, useState } from "react";
import { User, Eye, EyeOff, ShieldAlert, ArrowLeft } from "lucide-react";
import { Conversation, Message } from "../../api/types";
import { useConversationMessages } from "../../api/conversations";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import { WindowBadge } from "./WindowBadge";
import { TakeoverButton } from "./TakeoverButton";
import { useAuth } from "../../auth/useAuth";
import { formatDateSeparator } from "../../lib/utils";
import { Skeleton } from "../../components/Input";

interface ThreadProps {
  conversation: Conversation;
  onBack?: () => void;
}

export const Thread: React.FC<ThreadProps> = ({ conversation, onBack }) => {
  const { user } = useAuth();
  const [showFullPhone, setShowFullPhone] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messages, isLoading } = useConversationMessages(conversation.id);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const isAdmin = user?.role === "admin";
  const displayPhone =
    isAdmin && showFullPhone && conversation.wa_id_full
      ? conversation.wa_id_full
      : conversation.wa_id_masked;

  return (
    <div className="flex h-full w-full flex-col bg-background/50">
      {/* Thread Header Bar */}
      <div className="flex h-16 items-center justify-between border-b border-border bg-card px-4 md:px-6">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="md:hidden rounded-lg p-1.5 hover:bg-accent text-muted-foreground mr-1"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
          )}

          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 text-white font-bold text-sm shadow-xs">
            {conversation.name ? conversation.name.slice(0, 2).toUpperCase() : <User className="h-5 w-5" />}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-sm text-foreground">
                {conversation.name || conversation.wa_id_masked}
              </h2>
            </div>

            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <span>{displayPhone}</span>
              {isAdmin && conversation.wa_id_full && (
                <button
                  onClick={() => setShowFullPhone(!showFullPhone)}
                  className="rounded p-0.5 hover:text-foreground text-muted-foreground transition-colors"
                  title={showFullPhone ? "Mask phone number" : "Unmask full phone number (Admin Only)"}
                >
                  {showFullPhone ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:block">
            <WindowBadge lastUserMsgAt={conversation.last_user_msg_at} />
          </div>

          <TakeoverButton conversationId={conversation.id} status={conversation.status} />
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 md:p-6 space-y-3"
      >
        {isLoading && (
          <div className="space-y-4 max-w-lg">
            <Skeleton className="h-16 w-3/4 rounded-2xl" />
            <Skeleton className="h-20 w-4/5 rounded-2xl ml-auto" />
            <Skeleton className="h-16 w-2/3 rounded-2xl" />
          </div>
        )}

        {!isLoading && messages && messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-center text-xs text-muted-foreground">
            No message history for this contact yet.
          </div>
        )}

        {!isLoading &&
          messages?.map((msg: Message, index: number) => {
            const prevMsg = index > 0 ? messages[index - 1] : null;
            const showDateSep =
              !prevMsg ||
              new Date(msg.created_at).toDateString() !== new Date(prevMsg.created_at).toDateString();

            return (
              <React.Fragment key={msg.id}>
                {showDateSep && (
                  <div className="flex items-center justify-center my-4">
                    <span className="rounded-full bg-muted/80 border border-border px-3 py-1 text-[11px] font-medium text-muted-foreground shadow-xs">
                      {formatDateSeparator(msg.created_at)}
                    </span>
                  </div>
                )}
                <MessageBubble message={msg} />
              </React.Fragment>
            );
          })}
      </div>

      {/* Composer Input */}
      <Composer
        conversationId={conversation.id}
        status={conversation.status}
        lastUserMsgAt={conversation.last_user_msg_at}
      />
    </div>
  );
};
