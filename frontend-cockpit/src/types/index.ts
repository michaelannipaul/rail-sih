export interface Task {
  task_id: string;
  department: string;
  description: string;
  severity: string;
  allocated_time: number;
  track_km_span: string;
  priority_score: number;
  explainability: { feature: string; impact: number }[];
}

export interface Block {
  block_id: string;
  section_id: string;
  scheduled_start: string;
  scheduled_end: string;
  duration: number;
  departments_involved: string[];
  status: 'PENDING_START' | 'ACTIVE' | 'EXTENSION_REQUESTED' | 'CLEARED_EARLY' | 'COMPLETED';
  priority: string;
  consolidated_tasks: Task[];
}

export interface Train {
  train_no: string;
  train_type: 'Express' | 'Sub-urban' | 'Freight';
  name: string;
  priority: string;
  scheduled_arrival: string;
  expected_arrival: string;
  delay_minutes: number;
}

export interface Alert {
  id: string;
  type: 'WARNING' | 'TRAIN IMPACT' | 'EARLY HANDOVER' | 'CONFLICT';
  severity: 'high' | 'medium' | 'low';
  title: string;
  message: string;
  timestamp: string;
  related_block_id?: string;
  affected_train?: string;
}

export interface KPI {
  id: string;
  label: string;
  value: string;
  unit: string;
  trend: 'up' | 'down' | 'neutral';
  trend_value: string;
  status: 'good' | 'warning' | 'bad';
}

export interface SimulationResult {
  total_passenger_delay_minutes: number;
  regulated_freight_trains: number;
  punctuality_impact_pct: number;
  conflict_warnings: string[];
}
