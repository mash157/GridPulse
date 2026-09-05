export interface TelemetryRecord {
  event_id: string;
  timestamp: string;
  region: string;
  substation_id: string;
  transformer_id: string;
  latitude: number;
  longitude: number;
  voltage_kv: number;
  current_amp: number;
  power_mw: number;
  frequency_hz: number;
  load_percent: number;
  power_factor: number;
  temperature_c: number;
  energy_generated_mwh: number;
  energy_consumed_mwh: number;
  outage_duration_min: number;
  communication_latency_ms: number;
  fault_indicator: number;
  anomaly_score: number;
  risk_score: number;
  status: "Normal" | "Low" | "Warning" | "High Risk" | "Critical";
  anomaly_type: string;
  voltage_deviation_kv?: number;
  frequency_deviation_hz?: number;
}

export interface TransformerSummary {
  transformer_id: string;
  substation_id: string;
  region: string;
  total_power_mw: number;
  avg_voltage_kv: number;
  avg_current_amp: number;
  avg_power_mw: number;
  avg_frequency_hz: number;
  avg_load_percent: number;
  avg_power_factor: number;
  avg_temperature_c: number;
  max_temperature_c: number;
  total_energy_generated_mwh: number;
  total_energy_consumed_mwh: number;
  avg_latency_ms: number;
  total_faults: number;
  max_risk_score: number;
  avg_risk_score: number;
  record_count: number;
  worst_status: string;
  status: string;
  dominant_anomaly_type: string;
  distinct_anomaly_types: number;
}

export interface RegionSummary {
  region: string;
  total_power_mw: number;
  avg_voltage_kv: number;
  avg_load_percent: number;
  avg_temperature_c: number;
  avg_power_factor: number;
  total_energy_generated_mwh: number;
  total_energy_consumed_mwh: number;
  total_faults: number;
  transformer_count: number;
  substation_count: number;
  max_risk_score: number;
  avg_risk_score: number;
  record_count: number;
}

export interface SubstationSummary {
  substation_id: string;
  region: string;
  total_power_mw: number;
  avg_voltage_kv: number;
  avg_load_percent: number;
  avg_temperature_c: number;
  avg_power_factor: number;
  total_energy_generated_mwh: number;
  total_energy_consumed_mwh: number;
  total_faults: number;
  transformer_count: number;
  max_risk_score: number;
  avg_risk_score: number;
  record_count: number;
}

export interface AnomalySummary {
  anomaly_type: string;
  status: string;
  anomaly_count: number;
  avg_risk_score: number;
  avg_load_percent: number;
  avg_temperature_c: number;
  avg_voltage_kv: number;
}

export interface HourlySummary {
  hour_of_day: number;
  total_power_mw: number;
  avg_load_percent: number;
  avg_temperature_c: number;
  avg_energy_generated_mwh: number;
  avg_energy_consumed_mwh: number;
  total_faults: number;
  record_count: number;
  avg_risk_score: number;
}

export interface DailySummary {
  date: string;
  total_power_mw: number;
  avg_load_percent: number;
  avg_temperature_c: number;
  total_energy_generated_mwh: number;
  total_energy_consumed_mwh: number;
  total_faults: number;
  record_count: number;
  avg_risk_score: number;
}

export interface SeveritySummary {
  status: string;
  count: number;
  avg_risk_score: number;
  avg_load_percent: number;
  avg_temperature_c: number;
}

export interface GridHealthData {
  health_score: number;
  status: string;
  total_transformers: number;
  active_transformers: number;
  critical_transformers: number;
  normal_count: number;
  low_count: number;
  warning_count: number;
  high_risk_count: number;
  critical_count: number;
  avg_voltage_stability: number;
  avg_frequency_stability: number;
  overload_rate: number;
  communication_failure_rate: number;
}

export interface DashboardSummary {
  total_generation_mw: number;
  total_consumption_mw: number;
  grid_load_percent: number;
  active_transformers: number;
  total_transformers: number;
  faults_detected: number;
  anomalies_detected: number;
  grid_health_score: number;
  generation_trend: number;
  consumption_trend: number;
  load_trend: number;
  transformer_trend: number;
  fault_trend: number;
  anomaly_trend: number;
  records_today: number;
}

export interface Chart3DData {
  scatter3d: {
    x: number[];
    y: number[];
    z: number[];
    text: string[];
    color: string[];
    name: string;
  }[];
}

export interface Alert {
  event_id: string;
  timestamp: string;
  transformer_id: string;
  substation_id: string;
  region: string;
  anomaly_type: string;
  risk_score: number;
  status: string;
  voltage_kv: number;
  temperature_c: number;
  load_percent: number;
}

export interface LiveEvent {
  event_id: string;
  timestamp: string;
  region: string;
  substation_id: string;
  transformer_id: string;
  voltage_kv: number;
  current_amp: number;
  power_mw: number;
  frequency_hz: number;
  load_percent: number;
  power_factor: number;
  temperature_c: number;
  fault_indicator: number;
  anomaly_score: number;
  risk_score: number;
  status: string;
  anomaly_type: string;
  message?: string;
}

export interface SubstationLocation {
  substation_id: string;
  lat: number;
  lon: number;
  region: string;
  name: string;
  status: string;
  transformer_count: number;
}

export interface FilterState {
  region: string;
  substation: string;
  transformer: string;
  status: string;
  anomalyTypes: string[];
  riskLevel: string;
  timeRange: string;
}

export type Theme = "light" | "dark";
