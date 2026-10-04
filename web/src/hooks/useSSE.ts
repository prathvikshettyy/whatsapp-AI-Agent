import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CONVERSATIONS_KEY, MESSAGES_KEY } from "../api/conversations";
import { Conversation, Message } from "../api/types";

export interface SSEEventData {
  event: "message.created" | "handoff.requested" | "conversation.updated" | "ping";
  data: any;
}

export function useSSE(onHandoffAlert?: (conversation: Conversation) => void) {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const reconnectAttemptsRef = useRef<number>(0);

  useEffect(() => {
    // Request notification permissions gracefully if supported
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {});
    }

    function connect() {
      // Connect to SSE endpoint (in mock mode, we can simulate periodic simulated events or listen to SSE)
      const url = `${import.meta.env.VITE_API_URL || ""}/stream`;
      const es = new EventSource(url, { withCredentials: true });
      eventSourceRef.current = es;

      es.onopen = () => {
        reconnectAttemptsRef.current = 0;
        // Invalidate conversations to ensure synchrony on reconnect
        queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
      };

      es.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          handleSSEMessage(payload);
        } catch {
          // ignore unparsable pings
        }
      };

      es.addEventListener("message.created", (e: any) => {
        try {
          const message: Message = JSON.parse(e.data);
          handleMessageCreated(message);
        } catch (err) {
          console.error("Failed to parse message.created event", err);
        }
      });

      es.addEventListener("handoff.requested", (e: any) => {
        try {
          const convo: Conversation = JSON.parse(e.data);
          handleHandoffRequested(convo);
        } catch (err) {
          console.error("Failed to parse handoff.requested event", err);
        }
      });

      es.onerror = () => {
        es.close();
        // Exponential backoff reconnect: 1s, 2s, 4s, max 15s
        const backoff = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 15000);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, backoff);
      };
    }

    function handleMessageCreated(message: Message) {
      const convId = message.conversation_id;

      // 1. Append message to thread cache with dedupe by message.id
      queryClient.setQueryData<Message[]>(MESSAGES_KEY(convId), (old = []) => {
        if (old.some((m) => m.id === message.id)) {
          return old;
        }
        return [...old, message];
      });

      // 2. Bump conversation to top of list and update preview
      queryClient.setQueriesData<Conversation[]>({ queryKey: CONVERSATIONS_KEY }, (old = []) => {
        const found = old.find((c) => c.id === convId);
        const updated = old.map((c) =>
          c.id === convId
            ? {
                ...c,
                last_message_preview: message.content,
                last_user_msg_at: message.role === "user" ? message.created_at : c.last_user_msg_at,
                unread: message.role === "user" ? c.unread + 1 : c.unread,
              }
            : c
        );
        if (found) {
          const target = updated.find((c) => c.id === convId)!;
          return [target, ...updated.filter((c) => c.id !== convId)];
        }
        return updated;
      });
    }

    function handleHandoffRequested(convo: Conversation) {
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });

      if (onHandoffAlert) {
        onHandoffAlert(convo);
      }

      // Browser push notification if permitted
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("WhatsApp Human Agent Needed", {
          body: `${convo.name || convo.wa_id_masked}: ${convo.last_message_preview}`,
          icon: "/whatsapp-icon.png",
        });
      }
    }

    function handleSSEMessage(payload: any) {
      if (payload.event === "message.created") handleMessageCreated(payload.data);
      if (payload.event === "handoff.requested") handleHandoffRequested(payload.data);
    }

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [queryClient, onHandoffAlert]);
}
