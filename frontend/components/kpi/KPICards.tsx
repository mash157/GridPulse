"use client";

import {
  Zap,
  Battery,
  Gauge,
  Box,
  AlertTriangle,
  Activity,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

interface KPICardsProps {
  summary: any;
}

interface KPICard {
  label: string;
  value: string;
  icon: any;
  trend: number;
  trendLabel: string;
  color: string;
  className: string;
  sparkData: number[];
}

// Decorative mini-trend derived from the actual metric value (no hardcoded
// analytics numbers — the value animates around the real KPI).
function sparkFromValue(value: number): number[] {
  if (!value || value <= 0) {
    return Array.from({ length: 12 }, (_, i) => 5 + Math.abs(Math.sin(i * 1.7)) * 6);
  }
  const points: number[] = [];
  for (let i = 0; i < 12; i++) {
    const wave = Math.sin(i * 0.9) * 0.06 + Math.sin(i * 2.3) * 0.03;
    points.push(Math.max(0, value * (1 + wave)));
  }
  return points;
}

export default function KPICards({ summary }: KPICardsProps) {
  const s = summary || {};
  const totalGen = s.total_generation_mw ?? 0;
  const totalCons = s.total_consumption_mw ?? 0;
  const gridLoad = s.grid_load_percent ?? 0;
  const activeT = s.active_transformers ?? 0;
  const totalT = s.total_transformers ?? 0;
  const faults = s.faults_detected ?? 0;
  const anomalies = s.anomalies_detected ?? 0;

  const cards: KPICard[] = [
    {
      label: "Total Generation",
      value: totalGen >= 1000 ? (totalGen / 1000).toFixed(2) + " GW" : totalGen.toFixed(0) + " MW",
      icon: Zap,
      trend: s.generation_trend ?? 0,
      trendLabel: "vs last 24h",
      color: "#22c55e",
      className: "gen",
      sparkData: sparkFromValue(totalGen),
    },
    {
      label: "Total Consumption",
      value: totalCons >= 1000 ? (totalCons / 1000).toFixed(2) + " GW" : totalCons.toFixed(0) + " MW",
      icon: Battery,
      trend: s.consumption_trend ?? 0,
      trendLabel: "vs last 24h",
      color: "#3b82f6",
      className: "cons",
      sparkData: sparkFromValue(totalCons),
    },
    {
      label: "Grid Load",
      value: gridLoad.toFixed(1) + "%",
      icon: Gauge,
      trend: s.load_trend ?? 0,
      trendLabel: "vs last 24h",
      color: "#f97316",
      className: "load",
      sparkData: sparkFromValue(gridLoad),
    },
    {
      label: "Active Transformers",
      value: `${activeT} / ${totalT}`,
      icon: Box,
      trend: s.transformer_trend ?? 0,
      trendLabel: "vs last 24h",
      color: "#06b6d4",
      className: "trans",
      sparkData: sparkFromValue(activeT || totalT),
    },
    {
      label: "Faults Detected",
      value: faults.toString(),
      icon: AlertTriangle,
      trend: -(s.fault_trend ?? 0),
      trendLabel: "vs last 24h",
      color: "#ef4444",
      className: "fault",
      sparkData: sparkFromValue(faults),
    },
    {
      label: "Anomalies",
      value: anomalies.toString(),
      icon: Activity,
      trend: -(s.anomaly_trend ?? 0),
      trendLabel: "vs last 24h",
      color: "#a855f7",
      className: "anom",
      sparkData: sparkFromValue(anomalies),
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-4">
      {cards.map((card) => (
        <div key={card.label} className={`kpi-card ${card.className}`}>
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: `${card.color}15` }}
              >
                <card.icon className="w-4 h-4" style={{ color: card.color }} />
              </div>
              <span className="text-[12px] text-[var(--gp-text-muted)] font-medium">
                {card.label}
              </span>
            </div>
          </div>
          <div className="text-[22px] font-bold text-[var(--gp-text)] tracking-tight mb-1">
            {card.value}
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              {card.trend >= 0 ? (
                <TrendingUp className="w-3 h-3" style={{ color: card.color }} />
              ) : (
                <TrendingDown className="w-3 h-3" style={{ color: card.color }} />
              )}
              <span className="text-[11px] font-semibold" style={{ color: card.color }}>
                {card.trend >= 0 ? "↑" : "↓"} {Math.abs(card.trend)}%
              </span>
              <span className="text-[10px] text-[var(--gp-text-dim)]">{card.trendLabel}</span>
            </div>
            {/* Mini sparkline */}
            <MiniSparkline data={card.sparkData} color={card.color} />
          </div>
        </div>
      ))}
    </div>
  );
}

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 56;
  const h = 20;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={w} height={h} className="flex-shrink-0">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
