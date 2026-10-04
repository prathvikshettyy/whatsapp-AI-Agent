import React from "react";
import { Clock, AlertTriangle } from "lucide-react";
import { getHoursRemainingIn24hWindow } from "../../lib/utils";

interface WindowBadgeProps {
  lastUserMsgAt: string;
}

export const WindowBadge: React.FC<WindowBadgeProps> = ({ lastUserMsgAt }) => {
  const hoursRemaining = getHoursRemainingIn24hWindow(lastUserMsgAt);
  const isExpired = hoursRemaining <= 0;

  if (isExpired) {
    return (
      <div
        className="inline-flex items-center gap-1.5 rounded-full border border-destructive/30 bg-destructive/10 px-2.5 py-0.5 text-xs font-semibold text-destructive"
        title="24-hour customer service window has expired. Meta policy requires an approved template message."
      >
        <AlertTriangle className="h-3 w-3" />
        <span>24h Window Expired</span>
      </div>
    );
  }

  const hours = Math.floor(hoursRemaining);
  const minutes = Math.floor((hoursRemaining - hours) * 60);

  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400"
      title="Free-form customer service messaging is active within 24h of the user's last message."
    >
      <Clock className="h-3 w-3 text-emerald-500" />
      <span>
        24h Window: {hours}h {minutes}m left
      </span>
    </div>
  );
};
