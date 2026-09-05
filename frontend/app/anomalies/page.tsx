"use client";

import { useGridData } from "@/hooks/useGridData";
import { useWebSocket } from "@/hooks/useWebSocket";
import Sidebar from "@/components/sidebar/Sidebar";
import Header from "@/components/header/Header";
import LiveFeed from "@/components/LiveFeed";
import { getRiskClass, ANOMALY_COLORS } from "@/lib/utils";

export default function AnomaliesPage() {
  const { anomalies, alerts, filters, updateFilter, clearFilters, summary, loading } = useGridData();
  const { status: wsStatus, backendStatus, liveEvents } = useWebSocket();

  const summaryData = anomalies?.length
    ? anomalies.reduce((acc: any, a: any) => {
        acc.total += a.anomaly_count || 0;
        if (a.status === "Critical") acc.critical += a.anomaly_count || 0;
        if (a.status === "High Risk") acc.high += a.anomaly_count || 0;
        if (a.status === "Warning") acc.warning += a.anomaly_count || 0;
        acc.types[a.anomaly_type] = (acc.types[a.anomaly_type] || 0) + (a.anomaly_count || 0);
        return acc;
      }, { total: 0, critical: 0, high: 0, warning: 0, types: {} as Record<string, number> })
    : { total: 0, critical: 0, high: 0, warning: 0, types: {} as Record<string, number> };

  const sortedTypes: [string, number][] = Object.entries(summaryData.types)
    .map(([k, v]) => [k, v as number] as [string, number])
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--gp-bg)]">
      <Sidebar filters={filters} updateFilter={updateFilter} clearFilters={clearFilters} systemStatus={summary} anomalyCount={summary?.anomalies_detected || 0} />
      <div className="flex-1 ml-[220px] flex flex-col min-w-0 overflow-hidden">
        <Header wsStatus={wsStatus} backendStatus={backendStatus} />
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="gp-card p-4">
            <div className="section-title text-[18px] mb-1">Anomaly Analytics</div>
            <div className="section-subtitle">Anomaly detection, classification, and impact analysis</div>
          </div>

          {/* Summary KPIs */}
          <div className="grid grid-cols-4 gap-4">
            <div className="kpi-card anom">
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Total Anomalies</div>
              <div className="text-[22px] font-bold text-[var(--gp-text)]">{summaryData.total.toLocaleString()}</div>
            </div>
            <div className="kpi-card fault">
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Critical</div>
              <div className="text-[22px] font-bold text-[#ef4444]">{summaryData.critical.toLocaleString()}</div>
            </div>
            <div className="kpi-card" style={{ borderTopColor: "#f97316" }}>
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">High Risk</div>
              <div className="text-[22px] font-bold text-[#f97316]">{summaryData.high.toLocaleString()}</div>
            </div>
            <div className="kpi-card" style={{ borderTopColor: "#f59e0b" }}>
              <div className="text-[11px] text-[var(--gp-text-muted)] font-medium mb-1">Warning</div>
              <div className="text-[22px] font-bold text-[#f59e0b]">{summaryData.warning.toLocaleString()}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Anomaly Types */}
            <div className="gp-card p-4">
              <div className="section-title mb-3">Anomaly Types</div>
              <div className="space-y-3">
                {sortedTypes.map(([type, count]) => {
                  const maxCount = Math.max(...sortedTypes.map(([, c]) => c));
                  const pct = maxCount > 0 ? ((count as number) / maxCount) * 100 : 0;
                  const color = ANOMALY_COLORS[type] || "#64748b";
                  return (
                    <div key={type}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[12px] text-[var(--gp-text)]">{type}</span>
                        <span className="text-[12px] font-semibold text-[var(--gp-text)]">{count}</span>
                      </div>
                      <div className="h-2 bg-[var(--gp-surface-3)] rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
                      </div>
                    </div>
                  );
                })}
                {sortedTypes.length === 0 && <div className="text-[13px] text-[var(--gp-text-muted)]">No anomaly data</div>}
              </div>
            </div>

            {/* Recent Anomalies */}
            <div className="gp-card p-4">
              <div className="section-title mb-3">Recent Anomalies</div>
              <table className="gp-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Event</th>
                    <th>Location</th>
                    <th>Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {(alerts || []).slice(0, 10).map((alert: any, i: number) => (
                    <tr key={i}>
                      <td className="font-mono text-[11px] text-[var(--gp-text-muted)] whitespace-nowrap">
                        {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }) : "N/A"}
                      </td>
                      <td className="text-[12px]">{alert.anomaly_type}</td>
                      <td className="text-[12px] text-[var(--gp-text-muted)]">{alert.substation_id}</td>
                      <td><span className={`status-badge ${getRiskClass(alert.risk_score || 0)}`}>{alert.status}</span></td>
                    </tr>
                  ))}
                  {(!alerts || alerts.length === 0) && <tr><td colSpan={4} className="text-center text-[13px] text-[var(--gp-text-muted)] p-4">No recent anomalies</td></tr>}
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
