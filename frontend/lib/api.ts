const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function buildQuery(params?: Record<string, string>): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(([, v]) => v !== "" && v !== undefined && v !== null);
  if (entries.length === 0) return "";
  return "?" + new URLSearchParams(entries).toString();
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }
    return res.json();
  }

  async getSummary(params?: Record<string, string>) {
    return this.fetch(`/api/summary${buildQuery(params)}`);
  }

  async getRegions(params?: Record<string, string>) {
    return this.fetch(`/api/regions${buildQuery(params)}`);
  }

  async getTransformers(params?: Record<string, string>) {
    return this.fetch(`/api/transformers${buildQuery(params)}`);
  }

  async getAnomalies(params?: Record<string, string>) {
    return this.fetch(`/api/anomalies${buildQuery(params)}`);
  }

  async getEnergy(params?: Record<string, string>) {
    return this.fetch(`/api/energy${buildQuery(params)}`);
  }

  async getGridHealth(params?: Record<string, string>) {
    return this.fetch(`/api/grid-health${buildQuery(params)}`);
  }

  async getRisk(params?: Record<string, string>) {
    return this.fetch(`/api/risk${buildQuery(params)}`);
  }

  async getAnalytics3D(params?: Record<string, string>) {
    return this.fetch(`/api/analytics/3d${buildQuery(params)}`);
  }

  async getAlerts(params?: Record<string, string>) {
    return this.fetch(`/api/anomalies${buildQuery({ ...params, alerts: "true" })}`);
  }

  async getStatus() {
    return this.fetch("/api/status");
  }

  async getSubstations(params?: Record<string, string>) {
    return this.fetch(`/api/substations${buildQuery(params)}`);
  }

  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`, {
        cache: "no-store",
        signal: AbortSignal.timeout(3000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }
}

export const api = new ApiClient();

export function getWsUrl(): string {
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  return `${wsBase}/ws/grid`;
}
