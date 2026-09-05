"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

import { getStatusColor, REGION_COLORS, ANOMALY_COLORS } from "@/lib/utils";

// --- Grid Health Distribution (Donut Chart) ---
interface GridHealthProps {
  gridHealth: any;
  regions?: any[];
  onFilterChange?: (filter: string, value: string) => void;
}
export function GridHealthDonut({ gridHealth, regions, onFilterChange }: GridHealthProps) {
  const gh = gridHealth || {};

  // Record-level status counts from the filtered Gold dataset. The dataset
  // uses the 5-band mapping (Normal/Low/Warning/High Risk/Critical); the
  // donut shows four categories with Low folded into Normal so that
  // Normal + Warning + High Risk + Critical always equals the filtered
  // record count (150,000 when unfiltered).
  const normal = (gh.normal_count ?? 0) + (gh.low_count ?? 0);
  const warning = gh.warning_count ?? 0;
  const highRisk = gh.high_risk_count ?? 0;
  const critical = gh.critical_count ?? 0;
  const totalRecords = normal + warning + highRisk + critical;

  const labels = ["Normal", "Warning", "High Risk", "Critical"];
  const values = [normal, warning, highRisk, critical];
  const colors = ["#22c55e", "#f59e0b", "#f97316", "#ef4444"];

  const fmt = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(n >= 100000 ? 0 : 1)}k` : `${n}`);

  return (
    <div className="gp-card p-4 flex flex-col" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="flex items-center justify-between mb-2">
        <div className="section-title">Grid Health Distribution</div>
        <span className="text-[10px] text-[var(--gp-text-dim)]">per telemetry record</span>
      </div>

      <div className="flex items-center gap-3 flex-1 min-h-0">
        <div className="flex-shrink-0">
          <Plot
            data={[
              {
                type: "pie",
                labels,
                values,
                hole: 0.6,
                marker: { colors },
                textinfo: "none",
                hoverinfo: "label+value+percent",
                hoverlabel: {
                  bgcolor: "#1a2234",
                  bordercolor: "#2d3a4f",
                  font: { color: "#f1f5f9", size: 12, family: "Inter" },
                },
              },
            ]}
            layout={{
              width: 160,
              height: 160,
              margin: { t: 0, b: 0, l: 0, r: 0 },
              showlegend: false,
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              annotations: [
                {
                  text: `<b style="font-size:15px">${fmt(totalRecords)}</b><br><span style="font-size:9px">Total records</span>`,
                  showarrow: false,
                  font: { size: 9, color: "var(--gp-text-muted)", family: "Inter" },
                },
              ],
            }}
            config={{ displayModeBar: false, staticPlot: true }}
            style={{ display: "block" }}
          />
        </div>
        <div className="flex-1 space-y-2 min-w-0">
          {labels.map((label, i) => (
            <div key={label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: colors[i] }} />
                <span className="text-[12px] text-[var(--gp-text)]">{label}</span>
              </div>
              <div className="text-[12px] font-semibold text-[var(--gp-text)]">
                {values[i].toLocaleString()}
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between pt-1 border-t" style={{ borderColor: "var(--gp-border)" }}>
            <span className="text-[12px] font-medium text-[var(--gp-text-muted)]">Filtered total</span>
            <span className="text-[12px] font-bold text-[var(--gp-text)]">{totalRecords.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Energy by Region (Bar Chart) ---
interface EnergyByRegionProps {
  regions: any[];
  timeRange?: string;
  onTimeRangeChange?: (value: string) => void;
}
export function EnergyByRegion({ regions, timeRange = "90d", onTimeRangeChange }: EnergyByRegionProps) {
  const regionData = regions || [];

  const sorted = [...regionData].sort(
    (a: any, b: any) => (b.total_energy_generated_mwh || 0) - (a.total_energy_generated_mwh || 0)
  );

  return (
    <div className="gp-card p-4"            style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="flex items-center justify-between mb-2">
        <div className="section-title">Energy by Region</div>
        <select
          className="text-[11px] bg-[var(--gp-surface-2)] border border-[var(--gp-border)] rounded px-2 py-1 text-[var(--gp-text-muted)] focus:outline-none cursor-pointer"
          value={timeRange}
          onChange={(e) => onTimeRangeChange?.(e.target.value)}
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      <Plot
        data={[
          {
            type: "bar",
            x: sorted.map((r: any) => r.region),
            y: sorted.map((r: any) => r.total_energy_generated_mwh || 0),
            marker: {
              color: sorted.map((r: any) => REGION_COLORS[r.region] || "#3b82f6"),
              opacity: 0.85,
            },
            hovertemplate: "%{x}: %{y:.0f} MWh<extra></extra>",
          },
        ]}
        layout={{
          autosize: true,
          height: 200,
          margin: { t: 5, b: 35, l: 40, r: 10 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { family: "Inter", size: 11, color: "#94a3b8" },
          xaxis: {
            tickfont: { size: 10 },
            gridcolor: "transparent",
            linecolor: "transparent",
          },
          yaxis: {
            title: { text: "Power (MWh)", font: { size: 10 } },
            tickfont: { size: 10 },
            gridcolor: "var(--gp-border)",
            gridwidth: 0.5,
            linecolor: "transparent",
          },
          bargap: 0.3,
        }}
        config={{ displayModeBar: false }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}

// --- Top Anomaly Types (Horizontal Bar) ---
interface AnomalyTypesProps {
  anomalies: any[];
}
export function TopAnomalyTypes({ anomalies }: AnomalyTypesProps) {
  const data = (anomalies || [])
    .filter((a: any) => a.anomaly_type !== "Normal")
    .sort((a: any, b: any) => (b.anomaly_count || 0) - (a.anomaly_count || 0))
    .slice(0, 5);

  const reversed = [...data].reverse();
  const maxVal = Math.max(...reversed.map((d: any) => d.anomaly_count || 1), 1);

  return (
    <div className="gp-card p-4 flex flex-col" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="section-title mb-3">Top Anomaly Types</div>
      <div className="space-y-3 flex-1">
        {reversed.map((item: any) => {
          const pct = ((item.anomaly_count || 0) / maxVal) * 100;
          const color = ANOMALY_COLORS[item.anomaly_type] || "#64748b";
          return (
            <div key={item.anomaly_type}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[12px] text-[var(--gp-text)]">{item.anomaly_type}</span>
                <span className="text-[12px] font-semibold text-[var(--gp-text)]">
                  {item.anomaly_count}
                </span>
              </div>
              <div className="h-2 bg-[var(--gp-surface-3)] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
        {reversed.length === 0 && (
          <div className="text-[13px] text-[var(--gp-text-muted)]">No anomaly data</div>
        )}
      </div>
    </div>
  );
}

// --- Power Generation vs Consumption (Area Chart) ---
interface PowerChartProps {
  hourly: any[];
  timeRange?: string;
  onTimeRangeChange?: (value: string) => void;
}
export function PowerGenerationConsumption({ hourly, timeRange = "90d", onTimeRangeChange }: PowerChartProps) {
  const data = hourly || [];

  const hours = data.map((d: any) => String(d.hour_of_day).padStart(2, "0") + ":00");
  const gen = data.map((d: any) => d.avg_energy_generated_mwh || 0);
  const cons = data.map((d: any) => d.avg_energy_consumed_mwh || 0);

  return (
    <div className="gp-card p-4 flex flex-col" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="flex items-center justify-between mb-2">
        <div className="section-title">Power Generation vs Consumption</div>
        <select
          className="text-[11px] bg-[var(--gp-surface-2)] border border-[var(--gp-border)] rounded px-2 py-1 text-[var(--gp-text-muted)] focus:outline-none cursor-pointer"
          value={timeRange}
          onChange={(e) => onTimeRangeChange?.(e.target.value)}
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>
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

      <div className="chart-flex">
      <Plot
        data={[
          {
            type: "scatter",
            mode: "lines",
            name: "Generation",
            x: hours,
            y: gen,
            fill: "tozeroy",
            fillcolor: "rgba(34, 197, 94, 0.08)",
            line: { color: "#22c55e", width: 2, shape: "spline" },
            hovertemplate: "Gen: %{y:.0f} MWh<extra></extra>",
          },
          {
            type: "scatter",
            mode: "lines",
            name: "Consumption",
            x: hours,
            y: cons,
            fill: "tozeroy",
            fillcolor: "rgba(59, 130, 246, 0.08)",
            line: { color: "#3b82f6", width: 2, shape: "spline" },
            hovertemplate: "Cons: %{y:.0f} MWh<extra></extra>",
          },
        ]}
        layout={{
          autosize: true,
          height: 230,
          margin: { t: 5, b: 35, l: 50, r: 10 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { family: "Inter", size: 10, color: "#94a3b8" },
          xaxis: {
            tickfont: { size: 9 },
            gridcolor: "transparent",
            linecolor: "transparent",
            dtick: 4,
          },
          yaxis: {
            title: { text: "Power (MWh)", font: { size: 10 } },
            tickfont: { size: 9 },
            gridcolor: "var(--gp-border)",
            gridwidth: 0.5,
            linecolor: "transparent",
          },
          showlegend: false,
          hovermode: "x unified",
        }}
        config={{ displayModeBar: false }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
      </div>
    </div>
  );
}
