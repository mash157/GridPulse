"use client";

import dynamic from "next/dynamic";
import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";
import { REGION_COLORS } from "@/lib/utils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function ReportsPage() {
  const { summary, regions, gridHealth, energy, anomalies, filters, updateFilter, clearFilters } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const gh = gridHealth || {};
  const s = summary || {};

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Reports</div>
            <div className="section-subtitle">Grid health, energy, anomaly, and risk summary reports</div>
          </div>

          {/* Grid Health Summary */}
          <div className="gp-card p-4">
            <div className="section-title mb-3">Grid Health Summary</div>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-[28px] font-bold text-[var(--gp-success)]">{gh.health_score || "--"}</div>
                <div className="text-[11px] text-[var(--gp-text-muted)]">Health Score</div>
              </div>
              <div className="text-center">
                <div className="text-[28px] font-bold text-[var(--gp-text)]">{gh.total_transformers || "--"}</div>
                <div className="text-[11px] text-[var(--gp-text-muted)]">Total Transformers</div>
              </div>
              <div className="text-center">
                <div className="text-[28px] font-bold text-[var(--gp-success)]">{gh.active_transformers || "--"}</div>
                <div className="text-[11px] text-[var(--gp-text-muted)]">Active</div>
              </div>
              <div className="text-center">
                <div className="text-[28px] font-bold text-[var(--gp-danger)]">{gh.critical_transformers || "--"}</div>
                <div className="text-[11px] text-[var(--gp-text-muted)]">Critical</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Energy Summary */}
            <div className="gp-card p-4">
              <div className="section-title mb-3">Energy Summary</div>
              <div className="space-y-2">
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Total Generated</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(s.total_generation_mw || 0).toLocaleString()} MW</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Total Consumed</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(s.total_consumption_mw || 0).toLocaleString()} MW</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Grid Load</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(s.grid_load_percent || 0).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Records Today</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(s.records_today || 0).toLocaleString()}</span></div>
              </div>
            </div>

            {/* Anomaly Summary */}
            <div className="gp-card p-4">
              <div className="section-title mb-3">Anomaly Summary</div>
              <div className="space-y-2">
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Total Anomalies</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(s.anomalies_detected || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Faults Detected</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(s.faults_detected || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Normal Count</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(gh.normal_count || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Warning Count</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(gh.warning_count || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">High Risk Count</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(gh.high_risk_count || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="text-[13px] text-[var(--gp-text-muted)]">Critical Count</span><span className="text-[13px] font-semibold text-[var(--gp-text)]">{(gh.critical_count || 0).toLocaleString()}</span></div>
              </div>
            </div>
          </div>

          {/* Regional Summary */}
          <div className="gp-card p-4">
            <div className="section-title mb-3">Regional Summary</div>
            <table className="gp-table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Power (MW)</th>
                  <th>Avg Load</th>
                  <th>Avg Temp</th>
                  <th>Transformers</th>
                  <th>Faults</th>
                  <th>Avg Risk</th>
                </tr>
              </thead>
              <tbody>
                {(regions || []).map((r: any) => (
                  <tr key={r.region}>
                    <td className="text-[12px] font-medium">{r.region}</td>
                    <td className="text-[12px]">{(r.total_power_mw || 0).toLocaleString()}</td>
                    <td className="text-[12px]">{(r.avg_load_percent || 0).toFixed(1)}%</td>
                    <td className="text-[12px]">{(r.avg_temperature_c || 0).toFixed(1)}°C</td>
                    <td className="text-[12px]">{r.transformer_count || 0}</td>
                    <td className="text-[12px]">{r.total_faults || 0}</td>
                    <td className="text-[12px]">{(r.avg_risk_score || 0).toFixed(1)}</td>
                  </tr>
                ))}
                {(!regions || regions.length === 0) && <tr><td colSpan={7} className="text-center text-[13px] text-[var(--gp-text-muted)] p-4">No regional data available</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
        <LiveFeed events={liveEvents} />
      </div>
    </div>
  );
}
