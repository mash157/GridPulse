"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  Sun,
  Moon,
  Bell,
  ChevronDown,
} from "lucide-react";
import { useTheme } from "@/components/ui/ThemeProvider";
import { useGridData } from "@/hooks/useGridData";

interface HeaderProps {
  wsStatus: string;
  backendStatus?: "online" | "offline";
}

export default function Header({ wsStatus, backendStatus = "online" }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  // One shared anomaly count from the backend, respecting the current global
  // filters — used by both the header bell and the sidebar Anomalies badge.
  const { summary } = useGridData();
  const anomalyCount = summary?.anomalies_detected || 0;
  const [mounted, setMounted] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState("--:--:--");
  const [dateStr, setDateStr] = useState("---");

  useEffect(() => {
    setMounted(true);
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
      setDateStr(
        now.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  // Determine status display based on independent API health + WebSocket states
  const getStatusDisplay = () => {
    if (backendStatus === "offline") {
      return { text: "OFFLINE", color: "var(--gp-danger)", dotClass: "offline-dot" };
    }
    // Backend is online
    if (wsStatus === "connected") {
      return { text: "LIVE", color: "var(--gp-success)", dotClass: "live-dot" };
    }
    if (wsStatus === "connecting") {
      return { text: "CONNECTING", color: "#eab308", dotClass: "bg-yellow-400 animate-pulse" };
    }
    // Backend online but WS disconnected — show connecting (retrying)
    return { text: "CONNECTING", color: "#eab308", dotClass: "bg-yellow-400 animate-pulse" };
  };

  const status = getStatusDisplay();

  return (
    <header
      className="h-[56px] flex items-center justify-between px-5 flex-shrink-0 border-b"
      style={{
        background: "var(--gp-surface)",
        borderColor: "var(--gp-border)",
      }}
    >
      {/* LEFT GROUP: Search */}
      <div className="flex items-center">
        <div className="relative w-[300px]">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
            style={{ color: "var(--gp-text-muted)" }}
          />
          <input
            type="text"
            placeholder="Search anything..."
            className="w-full pl-9 pr-12 py-2 rounded-lg text-[13px] focus:outline-none focus:border-[var(--gp-primary)]"
            style={{
              background: "var(--gp-surface-2)",
              border: "1px solid var(--gp-border)",
              color: "var(--gp-text)",
            }}
          />
          <kbd
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] px-1.5 py-0.5 rounded font-mono"
            style={{
              color: "var(--gp-text-dim)",
              background: "var(--gp-surface-3)",
              border: "1px solid var(--gp-border)",
            }}
          >
            Ctrl K
          </kbd>
        </div>
      </div>

      {/* RIGHT GROUP: Status, Date/Time, Theme, Notifications, Admin */}
      <div className="flex items-center gap-2">
        {/* Live Data Status */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
          style={{
            background: "var(--gp-surface-2)",
            border: "1px solid var(--gp-border)",
          }}
        >
          {status.dotClass === "live-dot" ? (
            <div className="live-dot" />
          ) : status.dotClass === "offline-dot" ? (
            <div className="offline-dot" />
          ) : (
            <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
          )}
          <span
            className="text-[12px] font-semibold"
            style={{ color: status.color }}
          >
            {status.text}
          </span>
        </div>

        {/* Date & Time */}
        <div
          className="text-[13px] font-medium whitespace-nowrap px-3 py-1.5 rounded-lg"
          style={{
            background: "var(--gp-surface-2)",
            border: "1px solid var(--gp-border)",
            color: "var(--gp-text-muted)",
          }}
          suppressHydrationWarning
        >
          {dateStr}{" "}
          <span style={{ color: "var(--gp-text-dim)" }}>
            {currentTime}
          </span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-9 h-9 rounded-lg flex items-center justify-center transition-colors"
          style={{
            background: "var(--gp-surface-2)",
            border: "1px solid var(--gp-border)",
          }}
          title="Toggle theme"
        >
          {mounted ? (
            theme === "dark" ? (
              <Sun className="w-4 h-4" style={{ color: "var(--gp-text-muted)" }} />
            ) : (
              <Moon className="w-4 h-4" style={{ color: "var(--gp-text-muted)" }} />
            )
          ) : (
            <div className="w-4 h-4" />
          )}
        </button>

        {/* Notifications → /anomalies */}
        <Link
          href="/anomalies"
          className="relative w-9 h-9 rounded-lg flex items-center justify-center transition-colors"
          style={{
            background: "var(--gp-surface-2)",
            border: "1px solid var(--gp-border)",
          }}
          title="View anomalies"
        >
          <Bell
            className="w-4 h-4"
            style={{ color: "var(--gp-text-muted)" }}
          />
          {anomalyCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
              {anomalyCount > 99 ? "99+" : anomalyCount}
            </span>
          )}
        </Link>

        {/* Admin Profile - RIGHTMOST */}
        <div className="relative flex items-center gap-2 pl-3 border-l" style={{ borderColor: "var(--gp-border)" }}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-[12px] font-bold">
              A
            </div>
            <div className="hidden lg:block text-left">
              <div
                className="text-[13px] font-semibold"
                style={{ color: "var(--gp-text)" }}
              >
                Admin
              </div>
              <div
                className="text-[10px]"
                style={{ color: "var(--gp-text-muted)" }}
              >
                Grid Operator
              </div>
            </div>
            <ChevronDown
              className="w-3.5 h-3.5"
              style={{ color: "var(--gp-text-dim)" }}
            />
          </button>
          {profileOpen && (
            <div
              className="absolute top-full right-0 mt-2 w-48 rounded-lg shadow-xl border z-50 py-1"
              style={{
                background: "var(--gp-surface)",
                borderColor: "var(--gp-border)",
              }}
            >
              <div
                className="px-3 py-2 text-[12px] font-medium cursor-pointer hover:opacity-80"
                style={{ color: "var(--gp-text)" }}
              >
                My Profile
              </div>
              <div
                className="px-3 py-2 text-[12px] font-medium cursor-pointer hover:opacity-80"
                style={{ color: "var(--gp-text)" }}
              >
                Settings
              </div>
              <div
                className="border-t my-1"
                style={{ borderColor: "var(--gp-border)" }}
              />
              <div
                className="px-3 py-2 text-[12px] font-medium cursor-pointer hover:opacity-80"
                style={{ color: "var(--gp-danger)" }}
              >
                Sign Out
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
