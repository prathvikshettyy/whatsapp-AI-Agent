import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import { Conversation, Message } from "./types";

export const CONVERSATIONS_KEY = ["conversations"];
export const MESSAGES_KEY = (id: string) => ["conversations", id, "messages"];

export function useConversations(filterStatus?: string, search?: string) {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY, { filterStatus, search }],
    queryFn: async () => {
      const data = await apiClient<{ items: Conversation[]; next_cursor: string | null }>(
        "/conversations"
      );
      let items = data.items || [];
      if (filterStatus && filterStatus !== "all") {
        items = items.filter((c) => c.status === filterStatus);
      }
      if (search) {
        const q = search.toLowerCase();
        items = items.filter(
          (c) =>
            c.name?.toLowerCase().includes(q) ||
            c.wa_id_masked.includes(q) ||
            c.last_message_preview.toLowerCase().includes(q)
        );
      }
      return items;
    },
    refetchInterval: 10000,
  });
}

export function useConversationMessages(conversationId?: string) {
  return useQuery({
    queryKey: conversationId ? MESSAGES_KEY(conversationId) : ["conversations", "none", "messages"],
    queryFn: async () => {
      if (!conversationId) return [];
      const res = await apiClient<{ items: Message[]; next_cursor: string | null }>(
        `/conversations/${conversationId}/messages`
      );
      return res.items || [];
    },
    enabled: Boolean(conversationId),
  });
}

export function useTakeover(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return apiClient<{ status: string; success: boolean }>(
        `/conversations/${conversationId}/takeover`,
        { method: "POST" }
      );
    },
    onMutate: async () => {
      // Optimistic update on conversation list
      await queryClient.cancelQueries({ queryKey: CONVERSATIONS_KEY });
      const previous = queryClient.getQueryData<Conversation[]>(CONVERSATIONS_KEY);
      queryClient.setQueriesData<Conversation[]>(
        { queryKey: CONVERSATIONS_KEY },
        (old) =>
          old?.map((c) => (c.id === conversationId ? { ...c, status: "human" } : c))
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(CONVERSATIONS_KEY, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });
}

export function useRelease(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return apiClient<{ status: string; success: boolean }>(
        `/conversations/${conversationId}/release`,
        { method: "POST" }
      );
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: CONVERSATIONS_KEY });
      const previous = queryClient.getQueryData<Conversation[]>(CONVERSATIONS_KEY);
      queryClient.setQueriesData<Conversation[]>(
        { queryKey: CONVERSATIONS_KEY },
        (old) =>
          old?.map((c) => (c.id === conversationId ? { ...c, status: "bot" } : c))
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(CONVERSATIONS_KEY, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (content: string) => {
      return apiClient<Message>(`/conversations/${conversationId}/send`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
    },
    onMutate: async (content: string) => {
      // Optimistic message append
      await queryClient.cancelQueries({ queryKey: MESSAGES_KEY(conversationId) });
      const previousMessages = queryClient.getQueryData<Message[]>(MESSAGES_KEY(conversationId)) || [];
      const optimisticMsg: Message = {
        id: `temp_${Date.now()}`,
        conversation_id: conversationId,
        role: "staff",
        content,
        created_at: new Date().toISOString(),
        pending: true,
      };

      queryClient.setQueryData<Message[]>(
        MESSAGES_KEY(conversationId),
        [...previousMessages, optimisticMsg]
      );

      // Update preview in list
      queryClient.setQueriesData<Conversation[]>(
        { queryKey: CONVERSATIONS_KEY },
        (old) =>
          old?.map((c) =>
            c.id === conversationId ? { ...c, last_message_preview: content } : c
          )
      );

      return { previousMessages };
    },
    onError: (_err, _content, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(MESSAGES_KEY(conversationId), context.previousMessages);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: MESSAGES_KEY(conversationId) });
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });
}
