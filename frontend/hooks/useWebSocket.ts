"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api, getWsUrl } from "@/lib/api";
import type { LiveEvent } from "@/types/gridpulse";

type WsConnectionStatus = "idle" | "connecting" | "connected" | "disconnected";
type BackendHealthStatus = "online" | "offline";

export function useWebSocket(onEvent?: (event: LiveEvent) => void) {
  const [wsConnStatus, setWsConnStatus] = useState<WsConnectionStatus>("idle");
  const [backendHealth, setBackendHealth] = useState<BackendHealthStatus>("offline");
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<LiveEvent | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const healthTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  // Keep onEvent callback ref fresh
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  // ── Health check: runs independently on an interval ────────────────
  useEffect(() => {
    mountedRef.current = true;

    const checkHealth = async () => {
      if (!mountedRef.current) return;
      try {
        const isHealthy = await api.healthCheck();
        if (mountedRef.current) {
          setBackendHealth(isHealthy ? "online" : "offline");
        }
      } catch {
        if (mountedRef.current) {
          setBackendHealth("offline");
        }
      }
    };

    // Initial check
    checkHealth();
    healthTimer.current = setInterval(checkHealth, 5000);

    return () => {
      mountedRef.current = false;
      if (healthTimer.current) clearInterval(healthTimer.current);
    };
  }, []);

  // ── WebSocket: connect / reconnect ─────────────────────────────────
  const connect = useCallback(() => {
    // Guard: don't open if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    // Close any stale socket
    if (wsRef.current) {
      try { wsRef.current.close(); } catch {}
      wsRef.current = null;
    }

    try {
      setWsConnStatus("connecting");
      console.log("[WS] connecting...");
      const ws = new WebSocket(getWsUrl());

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        console.log("[WS] connected");
        setWsConnStatus("connected");
        setBackendHealth("online");
      };

      ws.onmessage = (e) => {
        try {
          const event: LiveEvent = JSON.parse(e.data);
          console.log("[WS] message received");
          setLatestEvent(event);
          setLiveEvents((prev) => [event, ...prev].slice(0, 50));
          onEventRef.current?.(event);
        } catch {}
      };

      ws.onclose = (event) => {
        console.log("[WS] disconnected", event.code);
        if (!mountedRef.current) return;
        setWsConnStatus("disconnected");
        // Auto-reconnect after 3 seconds
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error("[WS] error", err);
        // onclose will fire after onerror; reconnect handled there
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("[WS] connect failed", err);
      setWsConnStatus("disconnected");
      reconnectTimer.current = setTimeout(connect, 5000);
    }
  }, []);

  // Initial connection + cleanup
  useEffect(() => {
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        try { wsRef.current.close(); } catch {}
        wsRef.current = null;
      }
    };
  }, [connect]);

  // ── Derived display status ─────────────────────────────────────────
  // Header logic:
  //   API unreachable  → OFFLINE
  //   API reachable + WS connecting → CONNECTING
  //   API reachable + WS connected → LIVE
  //   API reachable + WS disconnected → CONNECTING (retrying)
  const displayStatus = backendHealth === "offline"
    ? "disconnected"       // Header will show OFFLINE
    : wsConnStatus === "connected"
      ? "connected"        // Header will show LIVE
      : "connecting";      // Header will show CONNECTING

  return {
    status: displayStatus,
    backendStatus: backendHealth,
    liveEvents,
    latestEvent,
    isConnected: displayStatus === "connected",
  };
}
