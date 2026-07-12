"use client";

import { useEffect } from "react";

/**
 * Connects to the backend SSE stream and triggers callbacks for relevant events.
 */
export function useEventStream(onEvent: (type: string, data: any) => void) {
  useEffect(() => {
    // Determine the base URL. If NEXT_PUBLIC_API_URL is set, use it.
    // Otherwise use relative path which is handled by next.config rewrites.
    let base = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
    
    // Fallback for development if not proxied
    if (typeof window !== "undefined" && window.location.port === "3000" && !process.env.NEXT_PUBLIC_API_URL) {
      base = "http://localhost:8000/api/v1";
    }

    const url = `${base}/events/stream`;
    const evtSource = new EventSource(url);

    evtSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload && payload.type) {
          onEvent(payload.type, payload.data);
        }
      } catch (err) {
        console.error("Failed to parse SSE event", err);
      }
    };

    evtSource.onerror = (err) => {
      console.error("SSE connection error", err);
    };

    return () => {
      evtSource.close();
    };
  }, [onEvent]);
}
