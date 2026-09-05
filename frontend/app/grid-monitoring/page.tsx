"use client";

import dynamic from "next/dynamic";
import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import GridMap from "@/components/grid_map/GridMap";
import LiveFeed from "@/components/LiveFeed";
import { REGION_COLORS } from "@/lib/utils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function GridMonitoringPage() {
  const { transformers, regions, summary, gridHealth, energy, filters, updateFilter, clearFilters } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const gh = gridHealth || {};
  const hourly = energy?.hourly || [];
  const hours = hourly.map((d: any) => String(d.hour_of_day ?? 0).padStart(2, "0") + ":00");
  const gen = hourly.map((d: any) => d.avg_energy_generated_mwh || 0);
  const cons = hourly.map((d: any) => d.avg_energy_consumed_mwh || 0);
  const load = hourly.map((d: any) => d.avg_load_percent || 0);

  // Status counts from transformers (representative status = avg risk)
  const statusCounts = (transformers || []).reduce((acc: Record<string, number>, t: any) => {
    const s = t.status || t.worst_status || "Normal";
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Header */}
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Grid Monitoring</div>
            <div className="section-subtitle">Real-time power flow and equipment status across all regions</div>
          </div>

          {/* Grid Health KPIs */}
          <div className="grid grid-cols-5 gap-4">
            <div className="kpi-card gen">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Health Score</div>
              <div className="text-[22px] font-bold" style={{ color: "var(--gp-text)" }}>{gh.health_score || "--"}</div>
              <div className="text-[10px]" style={{ color: "var(--gp-text-dim)" }}>{gh.status || "Unknown"}</div>
            </div>
            <div className="kpi-card cons">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Total Generation</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{(energy?.total_generated || 0).toLocaleString()} MWh</div>
            </div>
            <div className="kpi-card load">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Avg Grid Load</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{(summary?.grid_load_percent || 0).toFixed(1)}%</div>
            </div>
            <div className="kpi-card fault">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Faults Detected</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{summary?.faults_detected || 0}</div>
            </div>
            <div className="kpi-card anom">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Active Transformers</div>
              <div className="text-[18px] font-bold" style={{ color: "var(--gp-text)" }}>{gh.active_transformers || 0} / {gh.total_transformers || 0}</div>
            </div>
          </div>

          {/* Status Distribution */}
          <div className="grid grid-cols-5 gap-3">
            {["Normal", "Low", "Warning", "High Risk", "Critical"].map((s) => (
              <div key={s} className="gp-card p-3 text-center">
                <div className="text-[18px] font-bold" style={{ color: ["#22c55e", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"][["Normal", "Low", "Warning", "High Risk", "Critical"].indexOf(s)] }}>
                  {statusCounts[s] || 0}
                </div>
                <div className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>{s}</div>
              </div>
            ))}
          </div>

          {/* Main Grid: Map + Charts */}
          <div className="grid grid-cols-12 gap-4">
            {/* Live Grid Map */}
            <div className="col-span-7">
              <GridMap transformers={transformers} regions={regions} filters={filters} />
            </div>

            {/* Right side: Power Flow + Load Trend */}
            <div className="col-span-5 space-y-4">
              {/* Power Generation vs Consumption */}
              <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
                <div className="section-title mb-2">Power Flow</div>
                <div className="flex items-center gap-4 mb-2">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                    <span className="text-[11px] text-[var(--gp-text-muted)]">Generation</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                    <span className="text-[11px] text-[var(--gp-text-muted)]">Consumption</span>
                  </div>
                </div>
                <Plot
                  data={[
                    { type: "scatter", mode: "lines", name: "Gen", x: hours, y: gen, fill: "tozeroy", fillcolor: "rgba(34, 197, 94, 0.08)", line: { color: "#22c55e", width: 2, shape: "spline" }, hovertemplate: "Gen: %{y:.0f} MWh<extra></extra>" },
                    { type: "scatter", mode: "lines", name: "Cons", x: hours, y: cons, fill: "tozeroy", fillcolor: "rgba(59, 130, 246, 0.08)", line: { color: "#3b82f6", width: 2, shape: "spline" }, hovertemplate: "Cons: %{y:.0f} MWh<extra></extra>" },
                  ]}
                  layout={{ autosize: true, height: 180, margin: { t: 5, b: 30, l: 40, r: 10 }, paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: { family: "Inter", size: 10, color: "#94a3b8" }, xaxis: { tickfont: { size: 9 }, gridcolor: "transparent", dtick: 4 }, yaxis: { tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5 }, showlegend: false, hovermode: "x unified" }}
                  config={{ displayModeBar: false }}
                  style={{ width: "100%" }}
                  useResizeHandler
                />
              </div>

              {/* Grid Load Trend */}
              <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
                <div className="section-title mb-2">Grid Load Trend</div>
                <Plot
                  data={[{
                    type: "scatter", mode: "lines+markers", name: "Load %", x: hours, y: load,
                    line: { color: "#f97316", width: 2, shape: "spline" },
                    marker: { size: 3, color: "#f97316" },
                    fill: "tozeroy", fillcolor: "rgba(249, 115, 22, 0.08)",
                    hovertemplate: "Load: %{y:.1f}%<extra></extra>",
                  }]}
                  layout={{ autosize: true, height: 180, margin: { t: 5, b: 30, l: 40, r: 10 }, paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: { family: "Inter", size: 10, color: "#94a3b8" }, xaxis: { tickfont: { size: 9 }, gridcolor: "transparent", dtick: 4 }, yaxis: { title: { text: "Load %", font: { size: 10 } }, tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5 }, showlegend: false, hovermode: "x unified" }}
                  config={{ displayModeBar: false }}
                  style={{ width: "100%" }}
                  useResizeHandler
                />
              </div>
            </div>
          </div>

          {/* Regional Summary */}
          <div className="gp-card p-4">
            <div className="section-title mb-3">Regional Monitoring</div>
            <div className="grid grid-cols-6 gap-3">
              {(regions || []).map((r: any) => (
                <div key={r.region} className="p-3 rounded-lg border" style={{ borderColor: "var(--gp-border)", background: "var(--gp-surface-2)" }}>
                  <div className="text-[12px] font-semibold mb-1" style={{ color: REGION_COLORS[r.region] || "var(--gp-text)" }}>{r.region}</div>
                  <div className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>Load: <span className="font-semibold" style={{ color: "var(--gp-text)" }}>{(r.avg_load_percent || 0).toFixed(1)}%</span></div>
                  <div className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>Transformers: <span className="font-semibold" style={{ color: "var(--gp-text)" }}>{r.transformer_count || 0}</span></div>
                  <div className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>Faults: <span className="font-semibold" style={{ color: "var(--gp-text)" }}>{r.total_faults || 0}</span></div>
                  <div className="text-[11px]" style={{ color: "var(--gp-text-muted)" }}>Risk: <span className="font-semibold" style={{ color: "var(--gp-text)" }}>{(r.avg_risk_score || 0).toFixed(1)}</span></div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
