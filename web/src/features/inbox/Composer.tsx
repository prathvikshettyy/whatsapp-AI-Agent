import React, { useState } from "react";
import { Send, AlertTriangle, FileText, Lock, Sparkles } from "lucide-react";
import { Button } from "../../components/Button";
import { ConvStatus } from "../../api/types";
import { useSendMessage } from "../../api/conversations";
import { getHoursRemainingIn24hWindow } from "../../lib/utils";

interface ComposerProps {
  conversationId: string;
  status: ConvStatus;
  lastUserMsgAt: string;
}

export const Composer: React.FC<ComposerProps> = ({ conversationId, status, lastUserMsgAt }) => {
  const [text, setText] = useState("");
  const { mutate: sendMessage, isPending } = useSendMessage(conversationId);

  const hoursRemaining = getHoursRemainingIn24hWindow(lastUserMsgAt);
  const is24hExpired = hoursRemaining <= 0;
  const isHumanActive = status === "human";

  const handleSend = () => {
    if (!text.trim() || isPending || !isHumanActive || is24hExpired) return;
    const content = text.trim();
    setText("");
    sendMessage(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTemplateSelect = (templateText: string) => {
    setText(templateText);
  };

  return (
    <div className="border-t border-border bg-card p-3 md:p-4">
      {/* Bot Active Warning */}
      {!isHumanActive && (
        <div className="flex items-center justify-between rounded-xl bg-muted/60 p-3 text-xs text-muted-foreground border border-border">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-muted-foreground" />
            <span>AI Bot is currently handling this conversation. Take over above to reply manually.</span>
          </div>
          <span className="font-semibold text-primary">Bot Mode</span>
        </div>
      )}

      {/* 24h Window Expired Warning & Template Selector */}
      {isHumanActive && is24hExpired && (
        <div className="space-y-2 mb-3">
          <div className="flex items-start gap-2.5 rounded-xl border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">24-Hour WhatsApp Service Window Expired</p>
              <p className="text-[11px] opacity-90 mt-0.5">
                Meta requires sending an approved Business Message Template to restart conversation with this user.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleTemplateSelect("Hi! We are following up regarding your recent inquiry. Please reply if you still need assistance.")}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-medium hover:bg-accent transition-colors"
            >
              <FileText className="h-3 w-3 text-primary" /> Template: Re-engagement Follow-up
            </button>
            <button
              onClick={() => handleTemplateSelect("Your order status has been updated. Please reply to this message to view details.")}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-2.5 py-1 text-xs font-medium hover:bg-accent transition-colors"
            >
              <FileText className="h-3 w-3 text-primary" /> Template: Order Update
            </button>
          </div>
        </div>
      )}

      {/* Composer Input Box */}
      {isHumanActive && (
        <div className="flex flex-col gap-2">
          <div className="relative rounded-xl border border-input bg-background focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all shadow-xs">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                is24hExpired
                  ? "Select an approved template above to resume messaging..."
                  : "Type a WhatsApp reply... (Press ⌘+Enter to send)"
              }
              rows={3}
              className="w-full resize-none bg-transparent p-3 text-sm focus:outline-none placeholder:text-muted-foreground"
            />

            <div className="flex items-center justify-between border-t border-border/40 px-3 py-2 bg-muted/20 rounded-b-xl">
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className={text.length > 4000 ? "text-destructive font-bold" : ""}>
                  {text.length} / 4096 chars
                </span>
                <span className="hidden sm:inline">•</span>
                <span className="hidden sm:inline">Supports *bold*, _italic_, ~strike~</span>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={handleSend}
                  disabled={!text.trim() || isPending}
                  loading={isPending}
                  className="bg-[#25D366] text-white hover:bg-[#1faa53] gap-1.5 shadow-sm font-semibold"
                >
                  <span>Send</span>
                  <Send className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
