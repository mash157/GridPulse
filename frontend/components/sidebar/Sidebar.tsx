"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Radio,
  Zap,
  Box,
  AlertTriangle,
  TrendingUp,
  FileText,
  ChevronDown,
  ChevronRight,
  Activity,
  Clock,
  Database,
  Map,
  Settings,
  GitBranch,
} from "lucide-react";
import FilterSelect from "@/components/ui/FilterSelect";
import MultiSelectFilter from "@/components/ui/MultiSelectFilter";
import type { FilterState } from "@/types/gridpulse";

interface SidebarProps {
  filters: FilterState;
  updateFilter: (key: keyof FilterState, value: string | string[]) => void;
  clearFilters: () => void;
  systemStatus?: any;
  anomalyCount?: number;
}

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard, href: "/" },
  { id: "monitoring", label: "Grid Monitoring", icon: Radio, hasSubmenu: true, href: "/grid-monitoring" },
  { id: "transformers", label: "Transformers", icon: Zap, href: "/transformers" },
  { id: "3d", label: "3D Analytics", icon: Box, href: "/3d-analytics" },
  { id: "anomalies", label: "Anomalies", icon: AlertTriangle, href: "/anomalies" },
  { id: "forecasting", label: "Forecasting", icon: TrendingUp, href: "/forecasting" },
  { id: "reports", label: "Reports", icon: FileText, href: "/reports" },
];

const SUBMENU_ITEMS = [
  { label: "Live Map", href: "/grid-monitoring/live-map", icon: Map },
  { label: "Equipment Status", href: "/grid-monitoring/equipment-status", icon: Settings },
  { label: "Power Flow", href: "/grid-monitoring/power-flow", icon: GitBranch },
];

const REGIONS = ["North", "South", "East", "West"];
const SUBSTATIONS = ["SUB-001", "SUB-002", "SUB-003", "SUB-004", "SUB-005", "SUB-006", "SUB-007", "SUB-008", "SUB-009", "SUB-010", "SUB-011", "SUB-012", "SUB-013", "SUB-014", "SUB-015", "SUB-016", "SUB-017", "SUB-018", "SUB-019", "SUB-020", "SUB-021", "SUB-022", "SUB-023", "SUB-024", "SUB-025", "SUB-026", "SUB-027", "SUB-028", "SUB-029"];
const TRANSFORMERS = ["TR-001001", "TR-002001", "TR-003001", "TR-004001", "TR-005001"];
const RISK_LEVELS = ["Critical", "High Risk", "Warning", "Normal"];
const STATUSES = ["Normal", "Low", "Warning", "High Risk", "Critical"];
const ANOMALY_TYPES = ["Voltage Fluctuation", "Overload", "Temperature Spike", "Frequency Deviation", "Power Factor Anomaly", "Transformer Fault", "Communication Failure", "Unexpected Consumption", "Generation Drop", "Compound Anomaly"];
const TIME_RANGES = [
  { label: "Last 24 Hours", value: "24h" },
  { label: "Last 7 Days", value: "7d" },
  { label: "Last 30 Days", value: "30d" },
  { label: "Last 90 Days", value: "90d" },
  { label: "Last 72 Hours", value: "72h" },
  { label: "Last 6 Hours", value: "6h" },
  { label: "Last 12 Hours", value: "12h" },
  { label: "Last 48 Hours", value: "48h" },
];

export default function Sidebar({ filters, updateFilter, clearFilters, systemStatus, anomalyCount }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [expandedSub, setExpandedSub] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const getActiveNav = (): string => {
    const subMatch = SUBMENU_ITEMS.find((s) => pathname === s.href);
    if (subMatch) return "monitoring";
    const mainMatch = NAV_ITEMS.find((item) => pathname === item.href);
    if (mainMatch) return mainMatch.id;
    if (pathname.startsWith("/grid-monitoring")) return "monitoring";
    return "overview";
  };

  const activeNav = getActiveNav();

  useEffect(() => {
    if (pathname.startsWith("/grid-monitoring")) {
      setExpandedSub("monitoring");
    }
  }, [pathname]);

  const isSubActive = (href: string) => pathname === href;

  return (
    <aside
      className="fixed left-0 top-0 bottom-0 w-[220px] flex flex-col z-50 border-r overflow-hidden"
      style={{
        background: "var(--gp-sidebar-bg)",
        borderColor: "var(--gp-sidebar-border)",
      }}
    >
      {/* Logo - fixed height */}
      <div className="px-4 py-3 flex items-center gap-3 flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
          <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
        </div>
        <div>
          <div className="text-[14px] font-bold tracking-tight" style={{ color: "var(--gp-sidebar-logo-text)" }}>GridPulse</div>
          <div className="text-[9px] leading-tight" style={{ color: "var(--gp-sidebar-text)" }}>Smart Energy Grid Monitoring</div>
        </div>
      </div>

      {/* Navigation - takes remaining space, scrollable */}
      <nav className="flex-1 min-h-0 px-2 py-1 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <div key={item.id}>
            <Link
              href={item.href}
              onClick={(e) => {
                if (item.hasSubmenu) {
                  e.preventDefault();
                  setExpandedSub(expandedSub === item.id ? null : item.id);
                  if (!pathname.startsWith(item.href) || pathname === item.href) {
                    router.push(item.href);
                  }
                }
              }}
              className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all"
              style={{
                background: activeNav === item.id ? "var(--gp-sidebar-active)" : "transparent",
                color: activeNav === item.id ? "#ffffff" : "var(--gp-sidebar-text)",
              }}
              onMouseEnter={(e) => {
                if (activeNav !== item.id) {
                  e.currentTarget.style.background = "var(--gp-sidebar-hover)";
                }
              }}
              onMouseLeave={(e) => {
                if (activeNav !== item.id) {
                  e.currentTarget.style.background = "transparent";
                }
              }}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.id === "anomalies" && anomalyCount !== undefined && anomalyCount > 0 && (
                <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                  {anomalyCount > 99 ? "99+" : anomalyCount}
                </span>
              )}
              {item.hasSubmenu && (
                expandedSub === item.id
                  ? <ChevronDown className="w-3.5 h-3.5" />
                  : <ChevronRight className="w-3.5 h-3.5" />
              )}
            </Link>
            {item.hasSubmenu && expandedSub === item.id && (
              <div className="ml-4 mt-0.5 space-y-0.5">
                {SUBMENU_ITEMS.map((sub) => {
                  const isActive = isSubActive(sub.href);
                  return (
                    <Link
                      key={sub.href}
                      href={sub.href}
                      className="w-full flex items-center gap-2 px-3 py-1 text-[12px] rounded-md transition-all"
                      style={{
                        color: isActive ? "var(--gp-sidebar-active)" : "var(--gp-sidebar-text)",
                        background: isActive ? "var(--gp-sidebar-hover)" : "transparent",
                        fontWeight: isActive ? 600 : 400,
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.color = "var(--gp-sidebar-logo-text)";
                          e.currentTarget.style.background = "var(--gp-sidebar-hover)";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.color = "var(--gp-sidebar-text)";
                          e.currentTarget.style.background = "transparent";
                        }
                      }}
                    >
                      <sub.icon className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{sub.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* DATA FILTERS - scrollable section */}
      <div className="flex-shrink-0 border-t" style={{ borderColor: "var(--gp-sidebar-border)" }}>
        <div className="px-2.5 pt-2 pb-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider mb-1 px-1" style={{ color: "var(--gp-sidebar-text)" }}>
            DATA FILTERS
          </div>
        </div>
        <div className="px-2.5 pb-2 space-y-1.5 max-h-[35vh] overflow-y-auto">
          <FilterSelect
            label="Region"
            value={filters.region}
            options={[{ value: "", label: "All Regions" }, ...REGIONS.map((r) => ({ value: r, label: r }))]}
            onChange={(v) => updateFilter("region", v)}
            icon={<Radio className="w-3 h-3" />}
          />
          <FilterSelect
            label="Substation"
            value={filters.substation}
            options={[{ value: "", label: "All Substations" }, ...SUBSTATIONS.map((s) => ({ value: s, label: s }))]}
            onChange={(v) => updateFilter("substation", v)}
          />
          <FilterSelect
            label="Transformer"
            value={filters.transformer}
            options={[{ value: "", label: "All Transformers" }, ...TRANSFORMERS.map((t) => ({ value: t, label: t }))]}
            onChange={(v) => updateFilter("transformer", v)}
          />
          <FilterSelect
            label="Risk Level"
            value={filters.riskLevel}
            options={[{ value: "", label: "All Risk Levels" }, ...RISK_LEVELS.map((r) => ({ value: r.toLowerCase().replace(" ", "_"), label: r }))]}
            onChange={(v) => updateFilter("riskLevel", v)}
          />
          <FilterSelect
            label="Status"
            value={filters.status}
            options={[{ value: "", label: "All Statuses" }, ...STATUSES.map((s) => ({ value: s, label: s }))]}
            onChange={(v) => updateFilter("status", v)}
          />
          <MultiSelectFilter
            label="Anomaly Type(s)"
            selected={filters.anomalyTypes || []}
            options={ANOMALY_TYPES.map((a) => ({ value: a, label: a }))}
            onChange={(values) => updateFilter("anomalyTypes", values)}
          />
          <FilterSelect
            label="Time Range"
            value={filters.timeRange}
            options={TIME_RANGES}
            onChange={(v) => updateFilter("timeRange", v)}
            icon={<Clock className="w-3 h-3" />}
          />
        </div>
        <div className="px-2.5 pb-2">
          <button
            onClick={clearFilters}
            className="w-full text-white text-[12px] font-semibold py-1.5 rounded-lg transition-colors"
            style={{ background: "var(--gp-sidebar-active)" }}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* System Status - fixed at bottom */}
      <div className="px-3 py-2 border-t flex-shrink-0" style={{ borderColor: "var(--gp-sidebar-border)" }}>
        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: "var(--gp-sidebar-text)" }}>
          System Status
        </div>
        <div className="flex items-center gap-1.5 mb-0.5">
          <Activity className="w-3 h-3 text-green-500" />
          <span className="text-[11px] text-green-500 font-medium">All Systems Operational</span>
        </div>
        <div className="flex items-center gap-1.5 mb-0.5">
          <Database className="w-3 h-3" style={{ color: "var(--gp-sidebar-text)" }} />
          <span className="text-[11px]" style={{ color: "var(--gp-sidebar-text)" }}>Pipeline</span>
          <span className="text-[10px] text-green-500 font-medium ml-auto">Running</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px]" style={{ color: "var(--gp-sidebar-text)" }}>
          <Clock className="w-3 h-3" />
          <span suppressHydrationWarning>{systemStatus?.time || (mounted ? new Date().toLocaleTimeString("en-US", { hour12: false }) : "--:--:--")}</span>
        </div>
      </div>
    </aside>
  );
}
