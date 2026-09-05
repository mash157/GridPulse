"use client";

import Link from "next/link";
import { getRiskClass, formatPercent } from "@/lib/utils";

interface TransformerTableProps {
  transformers: any[];
}

export default function TransformerTable({ transformers }: TransformerTableProps) {
  const data = [...(transformers || [])]
      .sort((a: any, b: any) => (b.avg_risk_score || b.max_risk_score || 0) - (a.avg_risk_score || a.max_risk_score || 0))
      .slice(0, 6);

  return (
    <div className="gp-card p-4 flex flex-col" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="section-title">Top Risk Transformers</div>
        <Link
          href="/transformers"
          className="text-[11px] text-[var(--gp-primary)] font-medium hover:underline"
        >
          View All
        </Link>
      </div>
      <table className="gp-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Substation</th>
            <th>Risk</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((t: any) => {
            const risk = t.avg_risk_score || t.max_risk_score || 0;
            // Representative status (avg risk), consistent with the Transformers page
            const status = t.status || t.worst_status || "Normal";
            return (
              <tr key={t.transformer_id}>
                <td>
                  <span className="font-mono text-[12px] font-medium text-[var(--gp-text)]">
                    {t.transformer_id}
                  </span>
                </td>
                <td className="text-[12px] text-[var(--gp-text-muted)]">{t.substation_id}</td>
                <td>
                  <span className={`inline-flex items-center text-[12px] font-bold ${getRiskClass(risk)}`}>
                    {risk}
                  </span>
                </td>
                <td>
                  <span className={`status-badge ${getRiskClass(risk)}`}>
                    {status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
