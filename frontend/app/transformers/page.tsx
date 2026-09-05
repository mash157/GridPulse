"use client";

import dynamic from "next/dynamic";
import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";
import { getRiskClass, formatNumber } from "@/lib/utils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function TransformersPage() {
  const { transformers, filters, updateFilter, clearFilters, summary, loading } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const data = transformers || [];

  // Status counts from each transformer's representative status (avg risk)
  const statusCounts = data.reduce((acc: Record<string, number>, t: any) => {
    const s = t.status || t.worst_status || "Normal";
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const critical = statusCounts["Critical"] || 0;
  const highRisk = statusCounts["High Risk"] || 0;
  const warning = statusCounts["Warning"] || 0;
  const low = statusCounts["Low"] || 0;
  const normal = statusCounts["Normal"] || 0;

  // Top 10 by average risk
  const topRisk = [...data].sort((a: any, b: any) => (b.avg_risk_score || 0) - (a.avg_risk_score || 0)).slice(0, 10);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Transformers</div>
            <div className="section-subtitle">Transformer status, load, temperature, and risk analytics</div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-6 gap-4">
            <div className="kpi-card trans">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Total Transformers</div>
              <div className="text-[22px] font-bold" style={{ color: "var(--gp-text)" }}>{data.length}</div>
            </div>
            <div className="kpi-card" style={{ borderTopColor: "#22c55e" }}>
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Normal</div>
              <div className="text-[22px] font-bold" style={{ color: "#22c55e" }}>{normal}</div>
            </div>
            <div className="kpi-card" style={{ borderTopColor: "#3b82f6" }}>
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Low</div>
              <div className="text-[22px] font-bold" style={{ color: "#3b82f6" }}>{low}</div>
            </div>
            <div className="kpi-card" style={{ borderTopColor: "#f59e0b" }}>
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Warning</div>
              <div className="text-[22px] font-bold" style={{ color: "#f59e0b" }}>{warning}</div>
            </div>
            <div className="kpi-card" style={{ borderTopColor: "#f97316" }}>
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>High Risk</div>
              <div className="text-[22px] font-bold" style={{ color: "#f97316" }}>{highRisk}</div>
            </div>
            <div className="kpi-card fault">
              <div className="text-[11px] font-medium mb-1" style={{ color: "var(--gp-text-muted)" }}>Critical</div>
              <div className="text-[22px] font-bold" style={{ color: "#ef4444" }}>{critical}</div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Risk Distribution */}
            <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
              <div className="section-title mb-2">Transformer Risk Distribution</div>
              <Plot
                data={[{
                  type: "pie",
                  labels: ["Normal", "Low", "Warning", "High Risk", "Critical"],
                  values: [normal, low, warning, highRisk, critical],
                  hole: 0.5,
                  marker: { colors: ["#22c55e", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"] },
                  textinfo: "label+value",
                  textfont: { size: 10, family: "Inter", color: "var(--gp-text)" },
                  hoverinfo: "label+value+percent",
                }]}
                layout={{
                  autosize: true, height: 260,
                  margin: { t: 10, b: 10, l: 10, r: 10 },
                  paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                  showlegend: false,
                  annotations: [{ text: `<b>${data.length}</b><br>Transformers`, showarrow: false, font: { size: 14, color: "var(--gp-text)", family: "Inter" } }],
                }}
                config={{ displayModeBar: false, staticPlot: true }}
                style={{ width: "100%" }}
                useResizeHandler
              />
            </div>

            {/* Top Risk Transformers */}
            <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
              <div className="section-title mb-2">Top 10 Highest Risk Transformers</div>
              <Plot
                data={[{
                  type: "bar",
                  orientation: "h",
                  y: topRisk.map((t: any) => t.transformer_id),
                  x: topRisk.map((t: any) => t.avg_risk_score || 0),
                  marker: { color: topRisk.map((t: any) => {
                    const r = t.avg_risk_score || 0;
                    if (r >= 85) return "#ef4444";
                    if (r >= 70) return "#f97316";
                    if (r >= 50) return "#f59e0b";
                    if (r >= 30) return "#3b82f6";
                    return "#22c55e";
                  }), opacity: 0.85 },
                  hovertemplate: "%{y}: Risk %{x}<extra></extra>",
                }]}
                layout={{
                  autosize: true, height: 260,
                  margin: { t: 5, b: 30, l: 90, r: 20 },
                  paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                  font: { family: "Inter", size: 10, color: "#94a3b8" },
                  xaxis: { title: { text: "Risk Score", font: { size: 10 } }, tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5 },
                  yaxis: { tickfont: { size: 9 }, autorange: "reversed" },
                  bargap: 0.3,
                }}
                config={{ displayModeBar: false }}
                style={{ width: "100%" }}
                useResizeHandler
              />
            </div>
          </div>

          {/* Transformer Table */}
          <div className="gp-card overflow-hidden">
            <div className="px-4 py-3 border-b" style={{ borderColor: "var(--gp-border)" }}>
              <div className="section-title">All Transformers</div>
              <div className="section-subtitle mt-0.5">Aggregated Gold-dataset parameters per transformer — {data.length} of {summary?.total_transformers ?? data.length} assets shown</div>
            </div>
            <div className="overflow-x-auto">
              <table className="gp-table" style={{ minWidth: 1500 }}>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Substation</th>
                    <th>Region</th>
                    <th>Voltage (kV)</th>
                    <th>Current (A)</th>
                    <th>Power (MW)</th>
                    <th>Load %</th>
                    <th>Temp (°C)</th>
                    <th>Power Factor</th>
                    <th>Frequency (Hz)</th>
                    <th>Energy Gen (MWh)</th>
                    <th>Energy Cons (MWh)</th>
                    <th>Faults</th>
                    <th>Anomaly Type</th>
                    <th>Risk</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((t: any) => {
                    const risk = t.avg_risk_score || 0;
                    const status = t.status || t.worst_status || "Normal";
                    return (
                      <tr key={t.transformer_id}>
                        <td className="font-mono text-[12px] font-medium" style={{ color: "var(--gp-text)", whiteSpace: "nowrap" }}>{t.transformer_id}</td>
                        <td className="text-[12px]" style={{ color: "var(--gp-text-muted)", whiteSpace: "nowrap" }}>{t.substation_id}</td>
                        <td className="text-[12px]" style={{ color: "var(--gp-text-muted)" }}>{t.region}</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_voltage_kv || 0).toFixed(1)}</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_current_amp || 0).toFixed(1)}</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_power_mw || 0).toFixed(2)}</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_load_percent || 0).toFixed(1)}%</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_temperature_c || 0).toFixed(1)}</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_power_factor || 0).toFixed(3)}</td>
                        <td className="text-[12px] tabular-nums">{(t.avg_frequency_hz || 0).toFixed(2)}</td>
                        <td className="text-[12px] tabular-nums">{formatNumber(t.total_energy_generated_mwh || 0)}</td>
                        <td className="text-[12px] tabular-nums">{formatNumber(t.total_energy_consumed_mwh || 0)}</td>
                        <td className="text-[12px] tabular-nums">{t.total_faults || 0}</td>
                        <td className="text-[12px]" style={{ color: "var(--gp-text-muted)", whiteSpace: "nowrap" }}>{t.dominant_anomaly_type || "Normal"}</td>
                        <td className={`text-[12px] font-bold tabular-nums ${getRiskClass(risk)}`}>{Math.round(risk)}</td>
                        <td><span className={`status-badge ${getRiskClass(risk)}`}>{status}</span></td>
                      </tr>
                    );
                  })}
                  {data.length === 0 && !loading && (
                    <tr><td colSpan={16} className="text-center p-6" style={{ color: "var(--gp-text-muted)" }}>No transformer data available</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
