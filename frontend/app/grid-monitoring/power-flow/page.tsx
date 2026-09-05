"use client";

import dynamic from "next/dynamic";
import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";
import { REGION_COLORS } from "@/lib/utils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function PowerFlowPage() {
  const { energy, regions, summary, filters, updateFilter, clearFilters, gridHealth } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const hourly = energy?.hourly || [];
  const hours = hourly.map((d: any) => String(d.hour_of_day ?? 0).padStart(2, "0") + ":00");
  const gen = hourly.map((d: any) => d.avg_energy_generated_mwh || 0);
  const cons = hourly.map((d: any) => d.avg_energy_consumed_mwh || 0);
  const load = hourly.map((d: any) => d.avg_load_percent || 0);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Power Flow Analysis</div>
            <div className="section-subtitle">Generation, consumption, and load trend analysis across the grid</div>
          </div>

          {/* Power KPIs */}
          <div className="grid grid-cols-4 gap-4">
            <div className="kpi-card gen">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Total Generation</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{(energy?.total_generated || 0).toLocaleString()} MWh</div>
            </div>
            <div className="kpi-card cons">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Total Consumed</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{(energy?.total_consumed || 0).toLocaleString()} MWh</div>
            </div>
            <div className="kpi-card load">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Avg Grid Load</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{(summary?.grid_load_percent || 0).toFixed(1)}%</div>
            </div>
            <div className="kpi-card fault">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Faults Detected</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{summary?.faults_detected || 0}</div>
            </div>
          </div>

          {/* Generation vs Consumption Chart */}
          <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
            <div className="section-title mb-2">Power Generation vs Consumption</div>
            <div className="flex items-center gap-4 mb-2">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                <span className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>Generation</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                <span className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>Consumption</span>
              </div>
            </div>
            <Plot
              data={[
                { type: "scatter", mode: "lines", name: "Generation", x: hours, y: gen, fill: "tozeroy", fillcolor: "rgba(34, 197, 94, 0.08)", line: { color: "#22c55e", width: 2, shape: "spline" }, hovertemplate: "Gen: %{y:.0f} MWh<extra></extra>" },
                { type: "scatter", mode: "lines", name: "Consumption", x: hours, y: cons, fill: "tozeroy", fillcolor: "rgba(59, 130, 246, 0.08)", line: { color: "#3b82f6", width: 2, shape: "spline" }, hovertemplate: "Cons: %{y:.0f} MWh<extra></extra>" },
              ]}
              layout={{ autosize: true, height: 300, margin: { t: 10, b: 40, l: 50, r: 20 }, paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: { family: "Inter", size: 10, color: "#94a3b8" }, xaxis: { tickfont: { size: 9 }, gridcolor: "transparent", dtick: 4 }, yaxis: { title: { text: "MWh", font: { size: 10 } }, tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5 }, showlegend: false, hovermode: "x unified" }}
              config={{ displayModeBar: false }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          </div>

          {/* Grid Load Over Time */}
          <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
            <div className="section-title mb-2">Grid Load Trend</div>
            <Plot
              data={[{
                type: "scatter", mode: "lines+markers", name: "Load %", x: hours, y: load,
                line: { color: "#f97316", width: 2, shape: "spline" },
                marker: { size: 4, color: "#f97316" },
                fill: "tozeroy", fillcolor: "rgba(249, 115, 22, 0.08)",
                hovertemplate: "Load: %{y:.1f}%<extra></extra>",
              }]}
              layout={{ autosize: true, height: 250, margin: { t: 10, b: 40, l: 50, r: 20 }, paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: { family: "Inter", size: 10, color: "#94a3b8" }, xaxis: { tickfont: { size: 9 }, gridcolor: "transparent", dtick: 4 }, yaxis: { title: { text: "Load %", font: { size: 10 } }, tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5 }, showlegend: false, hovermode: "x unified" }}
              config={{ displayModeBar: false }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
