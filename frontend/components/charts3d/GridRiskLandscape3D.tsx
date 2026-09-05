"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  data3d: any;
}

export default function GridRiskLandscape3D({ data3d }: Props) {
  const riskData = data3d?.grid_risk || data3d?.risk_landscape || null;

  // Generate sample data if API doesn't provide it
  const scatter = riskData || generateRiskData();

  return (
    <div className="gp-card p-4" style={{ minWidth: 0, overflow: "hidden" }}>
      <div className="flex items-center justify-between mb-2">
        <div className="section-title">3D Grid Analytics</div>
        <Link
          href="/3d-analytics"
          className="text-[11px] text-[var(--gp-primary)] font-medium hover:underline"
        >
          View 3D
        </Link>
      </div>
      <div className="flex gap-2 mb-1">
        {["Normal", "Warning", "High Risk", "Critical"].map((label, i) => (
          <div key={label} className="flex items-center gap-1">
            <div
              className="w-2 h-2 rounded-full"
              style={{ background: ["#22c55e", "#f59e0b", "#f97316", "#ef4444"][i] }}
            />
            <span className="text-[10px] text-[var(--gp-text-muted)]">{label}</span>
          </div>
        ))}
      </div>

      <div className="chart-flex">
      <Plot
        data={scatter.traces || [
          {
            type: "scatter3d",
            mode: "markers",
            x: scatter.x,
            y: scatter.y,
            z: scatter.z,
            text: scatter.text,
            marker: {
              size: scatter.sizes || 3,
              color: scatter.color,
              opacity: 0.7,
            },
            hovertemplate: "%{text}<extra></extra>",
          },
        ]}
        layout={{
          autosize: true,
          height: 230,
          margin: { t: 0, b: 0, l: 0, r: 0 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { family: "Inter", size: 9, color: "#94a3b8" },
          scene: {
            xaxis: {
              title: { text: "Voltage (kV)", font: { size: 10 } },
              gridcolor: "var(--gp-border)",
              backgroundcolor: "transparent",
              showbackground: false,
              tickfont: { size: 8 },
            },
            yaxis: {
              title: { text: "Temperature (\u00B0C)", font: { size: 10 } },
              gridcolor: "var(--gp-border)",
              backgroundcolor: "transparent",
              showbackground: false,
              tickfont: { size: 8 },
            },
            zaxis: {
              title: { text: "Load (%)", font: { size: 10 } },
              gridcolor: "var(--gp-border)",
              backgroundcolor: "transparent",
              showbackground: false,
              tickfont: { size: 8 },
            },
            camera: {
              eye: { x: 1.5, y: 1.5, z: 1.0 },
            },
            bgcolor: "transparent",
          },
        }}
        config={{ displayModeBar: false }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
      </div>
    </div>
  );
}

function generateRiskData() {
  const n = 800;
  const x: number[] = [];
  const y: number[] = [];
  const z: number[] = [];
  const text: string[] = [];
  const color: string[] = [];
  const sizes: number[] = [];

  for (let i = 0; i < n; i++) {
    const voltage = 35 + Math.random() * 10;
    const temp = 35 + Math.random() * 50;
    let risk = (temp - 35) * 0.8 + Math.abs(voltage - 40) * 5 + Math.random() * 20;
    risk = Math.min(100, Math.max(0, risk));
    x.push(Math.round(voltage * 100) / 100);
    y.push(Math.round(temp * 100) / 100);
    z.push(Math.round(30 + Math.random() * 70));

    let status = "Normal";
    let c = "#22c55e";
    if (risk >= 85) { status = "Critical"; c = "#ef4444"; }
    else if (risk >= 70) { status = "High Risk"; c = "#f97316"; }
    else if (risk >= 50) { status = "Warning"; c = "#f59e0b"; }
    else if (risk >= 30) { status = "Low"; c = "#3b82f6"; }

    color.push(c);
    sizes.push(risk >= 70 ? 5 : risk >= 50 ? 4 : 3);
    text.push(
      `Voltage: ${x[i]} kV<br>Temp: ${y[i]}°C<br>Load: ${z[i]}%<br>Status: ${status}`
    );
  }

  return { x, y, z, text, color, sizes };
}
