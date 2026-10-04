import React from "react";
import { UserCheck, Bot } from "lucide-react";
import { Button } from "../../components/Button";
import { useRelease, useTakeover } from "../../api/conversations";
import { ConvStatus } from "../../api/types";
import { useToast } from "../../components/Toast";

interface TakeoverButtonProps {
  conversationId: string;
  status: ConvStatus;
}

export const TakeoverButton: React.FC<TakeoverButtonProps> = ({ conversationId, status }) => {
  const { mutate: takeover, isPending: isTakingOver } = useTakeover(conversationId);
  const { mutate: release, isPending: isReleasing } = useRelease(conversationId);
  const { toast } = useToast();

  const handleTakeover = () => {
    takeover(undefined, {
      onSuccess: () => {
        toast({
          title: "Conversation Taken Over",
          description: "AI bot replies are now paused. You can respond directly to the customer.",
          variant: "success",
        });
      },
      onError: (err: any) => {
        toast({
          title: "Takeover Failed",
          description: err.message || "Could not take over conversation.",
          variant: "destructive",
        });
      },
    });
  };

  const handleRelease = () => {
    release(undefined, {
      onSuccess: () => {
        toast({
          title: "Handed Back to Bot",
          description: "Claude AI assistant has resumed automated replies for this user.",
          variant: "default",
        });
      },
      onError: (err: any) => {
        toast({
          title: "Release Failed",
          description: err.message || "Could not release conversation to bot.",
          variant: "destructive",
        });
      },
    });
  };

  if (status === "human") {
    return (
      <Button
        variant="outline"
        size="sm"
        loading={isReleasing}
        onClick={handleRelease}
        className="border-emerald-600/40 text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/40 gap-1.5"
      >
        <Bot className="h-4 w-4 text-emerald-500" />
        <span>Release to Bot</span>
      </Button>
    );
  }

  return (
    <Button
      variant="default"
      size="sm"
      loading={isTakingOver}
      onClick={handleTakeover}
      className="bg-amber-600 hover:bg-amber-700 text-white gap-1.5 shadow-sm"
    >
      <UserCheck className="h-4 w-4" />
      <span>Take Over</span>
    </Button>
  );
};
