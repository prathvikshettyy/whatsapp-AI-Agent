import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import { KbArticle } from "./types";

export const KB_KEY = ["kb_articles"];

export function useKbArticles() {
  return useQuery({
    queryKey: KB_KEY,
    queryFn: () => apiClient<KbArticle[]>("/kb"),
  });
}

export function useCreateKbArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (article: Partial<KbArticle>) =>
      apiClient<KbArticle>("/kb", { method: "POST", body: JSON.stringify(article) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KB_KEY });
    },
  });
}

export function useUpdateKbArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...article }: Partial<KbArticle> & { id: string }) =>
      apiClient(`/kb/${id}`, { method: "PUT", body: JSON.stringify(article) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KB_KEY });
    },
  });
}

export function useDeleteKbArticle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient(`/kb/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KB_KEY });
    },
  });
}
