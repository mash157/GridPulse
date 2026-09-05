"use client";

import { useState, useEffect } from "react";
import { Zap } from "lucide-react";
import type { LiveEvent } from "@/types/gridpulse";

interface LiveFeedProps {
  events: LiveEvent[];
}

export default function LiveFeed({ events }: LiveFeedProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const items =
    events.length > 0
      ? events.slice(0, 10).map((e) => ({
          time: new Date(e.timestamp).toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }),
          message: `${e.anomaly_type !== "Normal" ? e.anomaly_type : "Normal operation"} at ${e.substation_id}`,
        }))
      : [];

  const duplicatedItems = [...items, ...items];

  return (
    <div className="h-[36px] bg-[var(--gp-surface)] border-t border-[var(--gp-border)] flex items-center overflow-hidden">
      <div className="flex items-center gap-2 px-4 border-r border-[var(--gp-border)] h-full flex-shrink-0">
        <Zap className="w-3.5 h-3.5 text-blue-500" />
        <span className="text-[12px] font-semibold text-[var(--gp-text)]">Live Feed</span>
      </div>
      <div className="ticker-wrapper flex-1">
        {mounted && duplicatedItems.length > 0 ? (
          <div className="ticker-content">
            {duplicatedItems.map((item, i) => (
              <span key={i} className="inline-flex items-center gap-2 mx-6">
                <span className="text-[11px] font-mono text-[var(--gp-primary)] font-medium">
                  {item.time}
                </span>
                <span className="text-[11px] text-[var(--gp-text-muted)]">
                  {item.message}
                </span>
              </span>
            ))}
          </div>
        ) : (
          <div className="flex items-center px-4 h-full">
            <span className="text-[11px] text-[var(--gp-text-dim)]">
              Waiting for live events...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
