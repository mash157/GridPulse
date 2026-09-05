export function cn(...inputs: (string | undefined | null | false)[]) {
  return inputs.filter(Boolean).join(" ");
}

export function formatNumber(n: number, decimals = 0): string {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toLocaleString("en-US", { maximumFractionDigits: decimals });
}

export function formatMW(n: number): string {
  if (Math.abs(n) >= 1000) return (n / 1000).toFixed(2) + " GW";
  return n.toFixed(1) + " MW";
}

export function formatPercent(n: number): string {
  return n.toFixed(1) + "%";
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "Critical": return "#ef4444";
    case "High Risk": return "#f97316";
    case "Warning": return "#f59e0b";
    case "Low": return "#3b82f6";
    case "Normal": return "#22c55e";
    default: return "#94a3b8";
  }
}

export function getStatusClass(status: string): string {
  switch (status) {
    case "Critical": return "status-critical";
    case "High Risk": return "status-high";
    case "Warning": return "status-warning";
    case "Normal":
    case "Low": return "status-normal";
    default: return "status-normal";
  }
}

export function getRiskClass(score: number): string {
  if (score >= 85) return "status-critical";
  if (score >= 70) return "status-high";
  if (score >= 50) return "status-warning";
  if (score >= 30) return "status-low";
  return "status-normal";
}

export function getRiskLabel(score: number): string {
  if (score >= 85) return "Critical";
  if (score >= 70) return "High Risk";
  if (score >= 50) return "Warning";
  if (score >= 30) return "Low";
  return "Normal";
}

export function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  } catch {
    return ts;
  }
}

export function formatDate(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return ts;
  }
}

export function timeAgo(ts: string): string {
  try {
    const now = new Date();
    const then = new Date(ts);
    const diff = now.getTime() - then.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return "";
  }
}

export const REGION_COLORS: Record<string, string> = {
  "North": "#3b82f6",
  "South": "#22c55e",
  "East": "#f59e0b",
  "West": "#ef4444",
  "Central": "#8b5cf6",
  "North-East": "#06b6d4",
};

export const ANOMALY_COLORS: Record<string, string> = {
  "Voltage Fluctuation": "#3b82f6",
  "Overload": "#ef4444",
  "Temperature Spike": "#f97316",
  "Frequency Deviation": "#06b6d4",
  "Power Factor Anomaly": "#8b5cf6",
  "Transformer Fault": "#dc2626",
  "Communication Failure": "#64748b",
  "Unexpected Consumption": "#f59e0b",
  "Generation Drop": "#22d3ee",
  "Compound Anomaly": "#e11d48",
  "Normal": "#22c55e",
};

export const SUBSTATION_COORDS: Record<string, { lat: number; lon: number; region: string; name: string }> = {
  "SUB-001": { lat: 28.6139, lon: 77.2090, region: "North", name: "Delhi" },
  "SUB-002": { lat: 26.9124, lon: 75.7873, region: "North", name: "Jaipur" },
  "SUB-003": { lat: 32.3246, lon: 74.7901, region: "North", name: "Jammu" },
  "SUB-004": { lat: 25.2048, lon: 77.3948, region: "North", name: "Lucknow" },
  "SUB-005": { lat: 19.0760, lon: 72.8777, region: "West", name: "Mumbai" },
  "SUB-006": { lat: 23.0225, lon: 72.5799, region: "West", name: "Ahmedabad" },
  "SUB-007": { lat: 18.5204, lon: 73.8567, region: "West", name: "Pune" },
  "SUB-008": { lat: 13.0827, lon: 80.2707, region: "South", name: "Chennai" },
  "SUB-009": { lat: 17.3850, lon: 78.4867, region: "South", name: "Hyderabad" },
  "SUB-010": { lat: 12.9716, lon: 77.5946, region: "South", name: "Bengaluru" },
  "SUB-011": { lat: 22.5726, lon: 88.3639, region: "East", name: "Kolkata" },
  "SUB-012": { lat: 23.2599, lon: 77.4126, region: "East", name: "Bhopal" },
  "SUB-013": { lat: 21.1466, lon: 79.0882, region: "East", name: "Nagpur" },
  "SUB-014": { lat: 26.8206, lon: 80.2701, region: "Central", name: "Varanasi" },
  "SUB-015": { lat: 25.3948, lon: 79.4625, region: "Central", name: "Prayagraj" },
  "SUB-016": { lat: 24.8688, lon: 76.6562, region: "Central", name: "Jhansi" },
  "SUB-017": { lat: 28.2960, lon: 76.5920, region: "North-East", name: "Meerut" },
  "SUB-018": { lat: 29.0588, lon: 76.0231, region: "North-East", name: "Panipat" },
  "SUB-019": { lat: 22.3167, lon: 78.0300, region: "West", name: "Indore" },
  "SUB-020": { lat: 25.5941, lon: 82.4720, region: "East", name: "Varanasi East" },
  "SUB-021": { lat: 19.6776, lon: 72.7323, region: "West", name: "Thane" },
  "SUB-022": { lat: 15.2993, lon: 74.1240, region: "South", name: "Hubli" },
  "SUB-023": { lat: 21.2787, lon: 82.1406, region: "East", name: "Jabalpur" },
  "SUB-024": { lat: 26.7461, lon: 78.9824, region: "North", name: "Bareilly" },
  "SUB-025": { lat: 24.4781, lon: 73.3114, region: "West", name: "Jaipur West" },
  "SUB-026": { lat: 17.3618, lon: 78.5310, region: "South", name: "Warangal" },
  "SUB-027": { lat: 28.5355, lon: 76.2346, region: "North-East", name: "Rohtak" },
  "SUB-028": { lat: 20.2884, lon: 76.2009, region: "Central", name: "Raipur" },
  "SUB-029": { lat: 26.9124, lon: 75.7873, region: "North", name: "Jaipur" },
};

export const TRANSMISSION_LINES: [string, string][] = [
  ["SUB-001", "SUB-002"],
  ["SUB-001", "SUB-004"],
  ["SUB-002", "SUB-024"],
  ["SUB-004", "SUB-014"],
  ["SUB-005", "SUB-007"],
  ["SUB-005", "SUB-021"],
  ["SUB-006", "SUB-019"],
  ["SUB-006", "SUB-025"],
  ["SUB-007", "SUB-019"],
  ["SUB-008", "SUB-010"],
  ["SUB-009", "SUB-010"],
  ["SUB-009", "SUB-026"],
  ["SUB-011", "SUB-012"],
  ["SUB-012", "SUB-023"],
  ["SUB-013", "SUB-023"],
  ["SUB-014", "SUB-015"],
  ["SUB-015", "SUB-016"],
  ["SUB-016", "SUB-028"],
  ["SUB-017", "SUB-027"],
  ["SUB-018", "SUB-027"],
  ["SUB-020", "SUB-011"],
  ["SUB-022", "SUB-010"],
];
