import { Block, Train, Alert, KPI } from '../../types';

export const mockBlocks: Block[] = [
  {
    block_id: 'BLK-2026-W36-004',
    section_id: 'HWH-BDC',
    scheduled_start: '01:30',
    scheduled_end: '05:00',
    duration: 210,
    departments_involved: ['Engineering', 'Signal & Telecom'],
    status: 'ACTIVE',
    priority: 'High',
    consolidated_tasks: [
      {
        task_id: 'TSK-1092',
        department: 'Engineering',
        description: 'Track renewal',
        severity: 'IMR',
        allocated_time: 180,
        track_km_span: 'Km 12-14',
        priority_score: 85.5,
        explainability: [
          { feature: 'IMR Severity Grade', impact: 28.4 },
          { feature: 'Track Density High', impact: 12.1 },
          { feature: 'Days Remaining to SLA', impact: 5.7 }
        ]
      }
    ]
  },
  {
    block_id: 'BLK-2026-W36-005',
    section_id: 'BDC-BWN',
    scheduled_start: '10:00',
    scheduled_end: '14:00',
    duration: 240,
    departments_involved: ['Electrical'],
    status: 'PENDING_START',
    priority: 'Medium',
    consolidated_tasks: [
      {
        task_id: 'TSK-1093',
        department: 'Electrical',
        description: 'OHE Maintenance',
        severity: 'Normal',
        allocated_time: 200,
        track_km_span: 'Km 45-50',
        priority_score: 65.0,
        explainability: [
          { feature: 'Maintenance Cycle', impact: 15.0 },
          { feature: 'Load Density', impact: 10.0 }
        ]
      }
    ]
  }
];

export const mockTrains: Train[] = [
  {
    train_no: '12303',
    train_type: 'Express',
    name: 'Poorva Express',
    priority: 'High',
    scheduled_arrival: '14:30',
    expected_arrival: '14:47',
    delay_minutes: 17
  },
  {
    train_no: '56821',
    train_type: 'Freight',
    name: 'BCN HL',
    priority: 'Low',
    scheduled_arrival: '15:00',
    expected_arrival: '15:24',
    delay_minutes: 24
  }
];

export const mockAlerts: Alert[] = [
  {
    id: 'ALT-01',
    type: 'WARNING',
    severity: 'high',
    title: 'Overdue Defect Flag',
    message: 'Task TSK-1092 (Track renewal) is past due-by date but remains unscheduled in tactical plan.',
    timestamp: '10:45'
  },
  {
    id: 'ALT-02',
    type: 'CONFLICT',
    severity: 'high',
    title: 'Corridor Slot Conflict',
    message: 'Unresolved slot conflict on HWH-BDC between Engineering and TRD requests. Manual resolution required.',
    timestamp: '10:50',
    related_block_id: 'BLK-2026-W36-004'
  },
  {
    id: 'ALT-03',
    type: 'TRAIN IMPACT',
    severity: 'medium',
    title: 'Punctuality Risk',
    message: 'Train 12303 expected delay: 17 minutes due to block extension.',
    timestamp: '11:00',
    affected_train: '12303'
  }
];

export const mockKPIs: KPI[] = [
  {
    id: 'kpi-1',
    label: 'Total Block Hours Saved',
    value: '18.5 hrs',
    unit: 'hrs',
    trend: 'up',
    trend_value: '12.4% vs previous planning',
    status: 'good'
  },
  {
    id: 'kpi-2',
    label: 'Asset Availability',
    value: '94.7',
    unit: '%',
    trend: 'up',
    trend_value: '2.1% from baseline',
    status: 'good'
  },
  {
    id: 'kpi-3',
    label: 'Disruption Reduction',
    value: '37.2',
    unit: '%',
    trend: 'down',
    trend_value: '5% improvement',
    status: 'good'
  },
  {
    id: 'kpi-4',
    label: 'Active Conflicts',
    value: '03',
    unit: '',
    trend: 'neutral',
    trend_value: 'Needs attention',
    status: 'warning'
  }
];

export const mockCorridors = [
  'HWH-BDC',
  'BDC-BWN',
  'BWN-KNJ',
  'NJP-SGU'
];
