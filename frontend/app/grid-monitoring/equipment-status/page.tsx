"use client";

import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";
import { getRiskClass, getStatusColor } from "@/lib/utils";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function EquipmentStatusPage() {
  const { transformers, filters, updateFilter, clearFilters, summary, gridHealth, risk } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const data = transformers || [];
  const gh = gridHealth || {};
  const r = risk || {};

  // Status distribution (representative status = avg risk)
  const statusDist = data.reduce((acc: Record<string, number>, t: any) => {
    const s = t.status || t.worst_status || "Normal";
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  const statuses = ["Normal", "Low", "Warning", "High Risk", "Critical"];
  const statusColors: Record<string, string> = {
    Normal: "#22c55e", Low: "#3b82f6", Warning: "#f59e0b", "High Risk": "#f97316", Critical: "#ef4444",
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Equipment Status</div>
            <div className="section-subtitle">Real-time equipment health and operational status monitoring</div>
          </div>

          {/* Status KPIs */}
          <div className="grid grid-cols-5 gap-4">
            {statuses.map((s) => (
              <div key={s} className="kpi-card">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full" style={{ background: statusColors[s] }} />
                  <span className="text-[12px] font-medium" style={{ color: "var(--gp-text-muted)" }}>{s}</span>
                </div>
                <div className="text-[22px] font-bold" style={{ color: "var(--gp-text)" }}>{statusDist[s] || 0}</div>
                <div className="text-[11px]" style={{ color: "var(--gp-text-dim)" }}>
                  {data.length > 0 ? ((statusDist[s] || 0) / data.length * 100).toFixed(1) : 0}% of total
                </div>
              </div>
            ))}
          </div>

          {/* Status Distribution Chart */}
          <div className="grid grid-cols-2 gap-4">
            <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
              <div className="section-title mb-2">Status Distribution</div>
              <Plot
                data={[{
                  type: "pie",
                  labels: statuses,
                  values: statuses.map((s) => statusDist[s] || 0),
                  hole: 0.5,
                  marker: { colors: statuses.map((s) => statusColors[s]) },
                  textinfo: "label+value",
                  textfont: { size: 10, color: "var(--gp-text)", family: "Inter" },
                  hoverinfo: "label+value+percent",
                }]}
                layout={{
                  autosize: true, height: 280,
                  margin: { t: 10, b: 10, l: 10, r: 10 },
                  paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                  showlegend: false,
                  annotations: [{
                    text: `<b>${data.length}</b><br>Total`,
                    showarrow: false,
                    font: { size: 16, color: "var(--gp-text)", family: "Inter" },
                  }],
                }}
                config={{ displayModeBar: false, staticPlot: true }}
                style={{ width: "100%" }}
                useResizeHandler
              />
            </div>

            <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
              <div className="section-title mb-2">Risk Score Distribution</div>
              <Plot
                data={[{
                  type: "bar",
                  x: statuses,
                  y: statuses.map((s) => statusDist[s] || 0),
                  marker: { color: statuses.map((s) => statusColors[s]), opacity: 0.85 },
                  hovertemplate: "%{x}: %{y}<extra></extra>",
                }]}
                layout={{
                  autosize: true, height: 280,
                  margin: { t: 10, b: 40, l: 40, r: 10 },
                  paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                  font: { family: "Inter", size: 10, color: "#94a3b8" },
                  xaxis: { tickfont: { size: 10 }, gridcolor: "transparent" },
                  yaxis: { title: { text: "Count", font: { size: 10 } }, tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5 },
                }}
                config={{ displayModeBar: false }}
                style={{ width: "100%" }}
                useResizeHandler
              />
            </div>
          </div>

          {/* Equipment Table */}
          <div className="gp-card overflow-hidden">
            <div className="px-4 py-3 border-b" style={{ borderColor: "var(--gp-border)" }}>
              <div className="section-title">Equipment Health Details</div>
            </div>
            <table className="gp-table">
              <thead>
                <tr>
                  <th>Transformer</th>
                  <th>Substation</th>
                  <th>Region</th>
                  <th>Avg Load</th>
                  <th>Temperature</th>
                  <th>Risk Score</th>
                  <th>Faults</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.slice(0, 20).map((t: any) => {
                  const risk = t.avg_risk_score || t.max_risk_score || 0;
                  const status = t.status || t.worst_status || "Normal";
                  return (
                    <tr key={t.transformer_id}>
                      <td className="font-mono text-[12px] font-medium" style={{ color: "var(--gp-text)" }}>{t.transformer_id}</td>
                      <td className="text-[12px]" style={{ color: "var(--gp-text-muted)" }}>{t.substation_id}</td>
                      <td className="text-[12px]" style={{ color: "var(--gp-text-muted)" }}>{t.region}</td>
                      <td className="text-[12px]">{(t.avg_load_percent || 0).toFixed(1)}%</td>
                      <td className="text-[12px]">{(t.avg_temperature_c || 0).toFixed(1)}°C</td>
                      <td className={`text-[12px] font-bold ${getRiskClass(risk)}`}>{risk.toFixed(0)}</td>
                      <td className="text-[12px]">{t.total_faults || 0}</td>
                      <td><span className={`status-badge ${getRiskClass(risk)}`}>{status}</span></td>
                    </tr>
                  );
                })}
                {data.length === 0 && (
                  <tr><td colSpan={8} className="text-center p-6" style={{ color: "var(--gp-text-muted)" }}>No equipment data available</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
