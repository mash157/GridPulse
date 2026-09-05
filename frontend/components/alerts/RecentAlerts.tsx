"use client";

import Link from "next/link";
import { getRiskClass, formatTimestamp } from "@/lib/utils";

interface AlertsProps {
  alerts: any[];
}

export default function RecentAlerts({ alerts }: AlertsProps) {
  const data = (alerts || []).slice(0, 5);

  return (
    <div className="gp-card p-4 flex flex-col" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="section-title">Recent Alerts</div>
        <Link
          href="/anomalies"
          className="text-[11px] text-[var(--gp-primary)] font-medium hover:underline"
        >
          View All
        </Link>
      </div>
      <div className="chart-flex overflow-hidden">
      <table className="gp-table" style={{ minHeight: 0 }}>
        <thead>
          <tr>
            <th>Time</th>
            <th>Event</th>
            <th>Location</th>
            <th>Severity</th>
          </tr>
        </thead>
        <tbody>
          {data.map((alert: any, i: number) => (
            <tr key={i}>
              <td className="font-mono text-[11px] text-[var(--gp-text-muted)] whitespace-nowrap">
                {formatTimestamp(alert.timestamp)}
              </td>
              <td className="text-[12px]">{alert.anomaly_type}</td>
              <td className="text-[12px] text-[var(--gp-text-muted)]">{alert.substation_id}</td>
              <td>
                <span className={`status-badge ${getRiskClass(alert.risk_score || 0)}`}>
                  {alert.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
