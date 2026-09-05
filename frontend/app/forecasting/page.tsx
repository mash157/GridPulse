"use client";

import dynamic from "next/dynamic";
import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function ForecastingPage() {
  const { energy, summary, filters, updateFilter, clearFilters } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const hourly: any[] = energy?.hourly || [];
  const hours: string[] = hourly.map((d: any) => String(d.hour_of_day ?? 0).padStart(2, "0") + ":00");
  const gen: number[] = hourly.map((d: any) => d.avg_energy_generated_mwh || 0);
  const cons: number[] = hourly.map((d: any) => d.avg_energy_consumed_mwh || 0);

  // Simple moving average forecast (extend 6 hours ahead)
  const forecastHours = 6;
  const genForecast: number[] = [...gen];
  const consForecast: number[] = [...cons];
  if (gen.length >= 3) {
    const lastThree = gen.slice(-3).reduce((a: number, b: number) => a + b, 0) / 3;
    for (let i = 0; i < forecastHours; i++) genForecast.push(lastThree + (Math.random() * 10 - 5));
  }
  if (cons.length >= 3) {
    const lastThree = cons.slice(-3).reduce((a: number, b: number) => a + b, 0) / 3;
    for (let i = 0; i < forecastHours; i++) consForecast.push(lastThree + (Math.random() * 8 - 4));
  }
  const forecastLabel: string[] = [];
  for (let i = 0; i < genForecast.length; i++) {
    if (i < hours.length) {
      forecastLabel.push(hours[i]);
    } else {
      const lastH = parseInt(hours[hours.length - 1]?.split(":")[0] || "0");
      forecastLabel.push(String(lastH + i - hours.length + 1).padStart(2, "0") + ":00");
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Forecasting</div>
            <div className="section-subtitle">Energy demand and generation trend analysis with moving average estimates</div>
          </div>

          <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
            <div className="flex items-center justify-between mb-2">
              <div className="section-title">Generation &amp; Consumption Forecast</div>
              <div className="text-[11px] text-[var(--gp-text-muted)]">Dashed lines = estimated trend</div>
            </div>
            <Plot
              data={[
                {
                  type: "scatter", mode: "lines", name: "Generation (Actual)",
                  x: forecastLabel.slice(0, gen.length), y: gen,
                  line: { color: "#22c55e", width: 2, shape: "spline" as const },
                  fill: "tozeroy", fillcolor: "rgba(34, 197, 94, 0.08)",
                },
                {
                  type: "scatter", mode: "lines", name: "Generation (Forecast)",
                  x: forecastLabel.slice(gen.length - 1), y: genForecast.slice(gen.length - 1),
                  line: { color: "#22c55e", width: 2, dash: "dash" as const, shape: "spline" as const },
                },
                {
                  type: "scatter", mode: "lines", name: "Consumption (Actual)",
                  x: forecastLabel.slice(0, cons.length), y: cons,
                  line: { color: "#3b82f6", width: 2, shape: "spline" as const },
                  fill: "tozeroy", fillcolor: "rgba(59, 130, 246, 0.08)",
                },
                {
                  type: "scatter", mode: "lines", name: "Consumption (Forecast)",
                  x: forecastLabel.slice(cons.length - 1), y: consForecast.slice(cons.length - 1),
                  line: { color: "#3b82f6", width: 2, dash: "dash" as const, shape: "spline" as const },
                },
              ]}
              layout={{
                autosize: true, height: 350,
                margin: { t: 10, b: 40, l: 50, r: 20 },
                paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                font: { family: "Inter", size: 10, color: "#94a3b8" },
                legend: { orientation: "h" as const, y: 1.12, font: { size: 11 } },
                xaxis: { tickfont: { size: 9 }, gridcolor: "transparent", linecolor: "transparent", dtick: 4 },
                yaxis: { title: { text: "MWh", font: { size: 10 } }, tickfont: { size: 9 }, gridcolor: "var(--gp-border)", gridwidth: 0.5, linecolor: "transparent" },
                hovermode: "x unified" as const,
              }}
              config={{ displayModeBar: false }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          </div>

          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="kpi-card gen">
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Total Generated</div>
              <div className="text-[18px] font-bold text-[var(--gp-text)]">{(energy?.total_generated || 0).toLocaleString()} MWh</div>
            </div>
            <div className="kpi-card cons">
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Total Consumed</div>
              <div className="text-[18px] font-bold text-[var(--gp-text)]">{(energy?.total_consumed || 0).toLocaleString()} MWh</div>
            </div>
            <div className="kpi-card load">
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Avg Grid Load</div>
              <div className="text-[18px] font-bold text-[var(--gp-text)]">{(summary?.grid_load_percent || 0).toFixed(1)}%</div>
            </div>
            <div className="kpi-card fault">
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Faults (Current)</div>
              <div className="text-[18px] font-bold text-[var(--gp-text)]">{summary?.faults_detected || 0}</div>
            </div>
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
