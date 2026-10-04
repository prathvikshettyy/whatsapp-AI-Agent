import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import { PromptVersion, SystemSettings } from "./types";

export const SETTINGS_KEY = ["settings"];
export const PROMPT_HISTORY_KEY = ["settings", "prompt-history"];

export function useSettings() {
  return useQuery({
    queryKey: SETTINGS_KEY,
    queryFn: () => apiClient<SystemSettings>("/settings"),
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (newSettings: Partial<SystemSettings> & { version_summary?: string }) =>
      apiClient<SystemSettings>("/settings", {
        method: "PUT",
        body: JSON.stringify(newSettings),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SETTINGS_KEY });
      queryClient.invalidateQueries({ queryKey: PROMPT_HISTORY_KEY });
    },
  });
}

export function usePromptHistory() {
  return useQuery({
    queryKey: PROMPT_HISTORY_KEY,
    queryFn: () => apiClient<PromptVersion[]>("/settings/prompt-history"),
  });
}
