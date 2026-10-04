import React from "react";
import { BarChart3, TrendingUp, Users, MessageSquare, Bot, Clock, DollarSign } from "lucide-react";
import { useAnalytics } from "../../api/analytics";
import { Skeleton } from "../../components/Input";

export const AnalyticsPage: React.FC = () => {
  const { data: stats, isLoading } = useAnalytics();

  if (isLoading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const cards = [
    {
      label: "Total Conversations",
      value: stats?.total_conversations.toLocaleString(),
      change: "+12.4% this week",
      icon: Users,
      color: "text-emerald-500",
    },
    {
      label: "Messages Processed Today",
      value: stats?.messages_today.toLocaleString(),
      change: "+8.1% vs yesterday",
      icon: MessageSquare,
      color: "text-primary",
    },
    {
      label: "Bot Resolution Rate",
      value: `${stats?.bot_resolution_rate}%`,
      change: "Auto-answered without human",
      icon: Bot,
      color: "text-teal-500",
    },
    {
      label: "Human Handoff Rate",
      value: `${stats?.handoff_rate}%`,
      change: "Requested staff takeover",
      icon: TrendingUp,
      color: "text-amber-500",
    },
    {
      label: "Avg AI Response Latency",
      value: `${stats?.avg_response_time_sec}s`,
      change: "Fast cloud reasoning",
      icon: Clock,
      color: "text-indigo-500",
    },
    {
      label: "Est. Claude API Spend",
      value: `$${stats?.estimated_token_cost_usd.toFixed(2)}`,
      change: "Cost today",
      icon: DollarSign,
      color: "text-emerald-600",
    },
  ];

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto p-4 md:p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-primary" />
          <span>Analytics & AI Performance</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Operational metrics, volume trends, bot resolution effectiveness, and API resource utilization.
        </p>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((c, idx) => {
          const Icon = c.icon;
          return (
            <div key={idx} className="rounded-2xl border border-border bg-card p-5 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">{c.label}</span>
                <Icon className={`h-4 w-4 ${c.color}`} />
              </div>
              <div className="mt-2 text-2xl font-extrabold text-foreground">{c.value}</div>
              <p className="text-[11px] text-muted-foreground mt-1">{c.change}</p>
            </div>
          );
        })}
      </div>

      {/* Daily Volume Visualizer */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-xs space-y-4">
        <h3 className="font-bold text-sm">7-Day WhatsApp Traffic Distribution</h3>

        <div className="grid grid-cols-7 gap-2 pt-6 items-end h-48 border-b border-border/60 pb-2">
          {stats?.daily_volume.map((item, idx) => {
            const maxVal = 500;
            const userHeight = Math.round((item.user_messages / maxVal) * 100);
            const botHeight = Math.round((item.bot_replies / maxVal) * 100);

            return (
              <div key={idx} className="flex flex-col items-center gap-2 h-full justify-end group">
                <div className="flex items-end gap-1.5 w-full justify-center h-full">
                  {/* User messages bar */}
                  <div
                    style={{ height: `${userHeight}%` }}
                    className="w-3 sm:w-4 rounded-t-md bg-[#25D366] transition-all group-hover:brightness-110"
                    title={`User messages: ${item.user_messages}`}
                  />
                  {/* Bot replies bar */}
                  <div
                    style={{ height: `${botHeight}%` }}
                    className="w-3 sm:w-4 rounded-t-md bg-primary/70 transition-all group-hover:brightness-110"
                    title={`Bot replies: ${item.bot_replies}`}
                  />
                </div>
                <span className="text-[11px] font-semibold text-muted-foreground">{item.date}</span>
              </div>
            );
          })}
        </div>

        <div className="flex items-center justify-center gap-6 pt-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-[#25D366]" />
            <span className="text-muted-foreground font-medium">User Incoming Messages</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-primary/70" />
            <span className="text-muted-foreground font-medium">Claude Automated Replies</span>
          </div>
        </div>
      </div>
    </div>
  );
};
