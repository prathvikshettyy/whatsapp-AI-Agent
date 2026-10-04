import { useQuery } from "@tanstack/react-query";
import { AnalyticsStats } from "./types";

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: async (): Promise<AnalyticsStats> => {
      // Mocked analytics metrics
      return {
        total_conversations: 1248,
        messages_today: 412,
        handoff_rate: 14.8, // 14.8%
        avg_response_time_sec: 1.8,
        bot_resolution_rate: 85.2,
        estimated_token_cost_usd: 12.45,
        daily_volume: [
          { date: "Mon", user_messages: 280, bot_replies: 310 },
          { date: "Tue", user_messages: 340, bot_replies: 375 },
          { date: "Wed", user_messages: 410, bot_replies: 440 },
          { date: "Thu", user_messages: 390, bot_replies: 420 },
          { date: "Fri", user_messages: 450, bot_replies: 490 },
          { date: "Sat", user_messages: 210, bot_replies: 230 },
          { date: "Sun", user_messages: 195, bot_replies: 215 },
        ],
      };
    },
  });
}
