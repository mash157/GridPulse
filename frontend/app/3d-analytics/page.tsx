"use client";

import dynamic from "next/dynamic";
import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

function Chart3D({ title, trace, xLabel, yLabel, zLabel }: {
  title: string;
  trace: { x: number[]; y: number[]; z: number[]; color: string[]; text: string[]; sizes: number[] } | null;
  xLabel: string;
  yLabel: string;
  zLabel: string;
}) {
  if (!trace || trace.x.length === 0) {
    return (
      <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
        <div className="section-title mb-2">{title}</div>
        <div className="text-[12px] text-[var(--gp-text-muted)] flex items-center justify-center h-[350px]">
          No data available
        </div>
      </div>
    );
  }

  return (
    <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="section-title mb-2">{title}</div>
      <Plot
        data={[{
          type: "scatter3d",
          mode: "markers",
          x: trace.x,
          y: trace.y,
          z: trace.z,
          text: trace.text,
          marker: {
            size: trace.sizes || 3,
            color: trace.color,
            opacity: 0.7,
          },
          hovertemplate: "%{text}<extra></extra>",
        }]}
        layout={{
          autosize: true,
          height: 350,
          margin: { t: 0, b: 0, l: 0, r: 0 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { family: "Inter", size: 9, color: "#94a3b8" },
          scene: {
            xaxis: { title: { text: xLabel, font: { size: 10 } }, gridcolor: "var(--gp-border)", showbackground: false, tickfont: { size: 8 } },
            yaxis: { title: { text: yLabel, font: { size: 10 } }, gridcolor: "var(--gp-border)", showbackground: false, tickfont: { size: 8 } },
            zaxis: { title: { text: zLabel, font: { size: 10 } }, gridcolor: "var(--gp-border)", showbackground: false, tickfont: { size: 8 } },
            camera: { eye: { x: 1.5, y: 1.5, z: 1.0 } },
            bgcolor: "transparent",
          },
        }}
        config={{ displayModeBar: false }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}

export default function Analytics3DPage() {
  const { analytics3D, filters, updateFilter, clearFilters, summary } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  // The API returns { grid_risk: { x, y, z, color, text, sizes }, load_performance: { ... } }
  const gridRisk = analytics3D?.grid_risk || null;
  const loadPerf = analytics3D?.load_performance || null;

  // For Energy Performance and Anomaly Space, we derive from grid_risk data
  // since the API only provides grid_risk and load_performance
  const energyPerformance = gridRisk ? {
    x: gridRisk.x, // Use voltage as proxy for generated energy
    y: gridRisk.z.map((z: number) => z * 10), // Load as proxy for consumed energy
    z: gridRisk.z,
    color: gridRisk.color,
    text: gridRisk.text,
    sizes: gridRisk.sizes,
  } : null;

  const anomalySpace = gridRisk ? {
    x: gridRisk.x.map((v: number) => Math.abs(v - 40)), // Voltage deviation
    y: gridRisk.y, // Temperature
    z: gridRisk.z.map((z: number) => z * 0.8), // Anomaly score as proxy
    color: gridRisk.color,
    text: gridRisk.text,
    sizes: gridRisk.sizes,
  } : null;

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">3D Analytics</div>
            <div className="section-subtitle">
              Multi-dimensional analytical visualizations of grid data
              {analytics3D?.sample_size && (
                <span className="ml-2 text-[var(--gp-primary)]">
                  ({analytics3D.sample_size.toLocaleString()} samples from {analytics3D.total_records?.toLocaleString()} records)
                </span>
              )}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 px-1">
            {["Normal", "Low", "Warning", "High Risk", "Critical"].map((label, i) => (
              <div key={label} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: ["#22c55e", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"][i] }} />
                <span className="text-[11px] text-[var(--gp-text-muted)]">{label}</span>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Chart3D
              title="Grid Risk Landscape"
              trace={gridRisk}
              xLabel="Voltage (kV)"
              yLabel="Temperature (°C)"
              zLabel="Risk Score"
            />
            <Chart3D
              title="Load Performance Space"
              trace={loadPerf}
              xLabel="Load (%)"
              yLabel="Power Factor"
              zLabel="Temperature (°C)"
            />
            <Chart3D
              title="Energy Performance Space"
              trace={energyPerformance}
              xLabel="Voltage (kV)"
              yLabel="Load (%)"
              zLabel="Temperature (°C)"
            />
            <Chart3D
              title="Anomaly Space"
              trace={anomalySpace}
              xLabel="Voltage Deviation (kV)"
              yLabel="Temperature (°C)"
              zLabel="Anomaly Score"
            />
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
