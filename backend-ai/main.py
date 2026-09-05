import csv
import io
from datetime import datetime
from typing import Literal
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="RailSync Operations API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory primary database for blocks and alerts
DATABASE = {
    "blocks": [
        {
            "block_id": "BLK-2026-W36-004",
            "section_id": "HWH-BDC",
            "scheduled_start": "01:30",
            "scheduled_end": "05:00",
            "duration": 210,
            "departments_involved": ["Engineering", "Signal & Telecom"],
            "status": "ACTIVE",
            "priority": "High",
            "consolidated_tasks": [
                {
                    "task_id": "TSK-1092",
                    "department": "Engineering",
                    "description": "Track renewal",
                    "severity": "IMR",
                    "allocated_time": 180,
                    "track_km_span": "Km 12-14",
                    "priority_score": 85.5,
                    "explainability": [
                        {"feature": "IMR Severity Grade", "impact": 28.4},
                        {"feature": "Track Density High", "impact": 12.1},
                        {"feature": "Days Remaining to SLA", "impact": 5.7},
                    ],
                }
            ],
            "decision": None,
            "decision_reason": None,
        },
        {
            "block_id": "BLK-2026-W36-005",
            "section_id": "BDC-BWN",
            "scheduled_start": "10:00",
            "scheduled_end": "14:00",
            "duration": 240,
            "departments_involved": ["Electrical"],
            "status": "PENDING_START",
            "priority": "Medium",
            "consolidated_tasks": [
                {
                    "task_id": "TSK-1093",
                    "department": "Electrical",
                    "description": "OHE Maintenance",
                    "severity": "Normal",
                    "allocated_time": 200,
                    "track_km_span": "Km 45-50",
                    "priority_score": 65.0,
                    "explainability": [
                        {"feature": "Maintenance Cycle", "impact": 15.0},
                        {"feature": "Load Density", "impact": 10.0},
                    ],
                }
            ],
            "decision": None,
            "decision_reason": None,
        },
    ],
    "trains": [
        {
            "train_no": "12303",
            "train_type": "Express",
            "name": "Poorva Express",
            "priority": "High",
            "scheduled_arrival": "14:30",
            "expected_arrival": "14:47",
            "delay_minutes": 17,
        },
        {
            "train_no": "56821",
            "train_type": "Freight",
            "name": "BCN HL",
            "priority": "Low",
            "scheduled_arrival": "15:00",
            "expected_arrival": "15:24",
            "delay_minutes": 24,
        },
    ],
    "alerts": [
        {
            "id": "ALT-01",
            "type": "WARNING",
            "severity": "high",
            "title": "Overdue Defect Flag",
            "message": "Task TSK-1092 (Track renewal) is past due-by date but remains unscheduled in tactical plan.",
            "timestamp": "10:45",
        },
        {
            "id": "ALT-02",
            "type": "CONFLICT",
            "severity": "high",
            "title": "Corridor Slot Conflict",
            "message": "Unresolved slot conflict on HWH-BDC between Engineering and TRD requests. Manual resolution required.",
            "timestamp": "10:50",
            "related_block_id": "BLK-2026-W36-004",
        },
        {
            "id": "ALT-03",
            "type": "TRAIN IMPACT",
            "severity": "medium",
            "title": "Punctuality Risk",
            "message": "Train 12303 expected delay: 17 minutes due to block extension.",
            "timestamp": "11:00",
            "affected_train": "12303",
        },
    ],
    "corridors": ["HWH-BDC", "BDC-BWN", "BWN-KNJ", "NJP-SGU"],
}


class SimulationRequest(BaseModel):
    block_id: str
    new_end_time: str


class DecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str | None = None
    operator_role: str | None = "COA"


def parse_minutes(time_str: str) -> int:
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "RailSync AI Operations API", "timestamp": datetime.now().isoformat()}


@app.get("/api/dashboard")
def dashboard(view_mode: str = "optimized", mode: str | None = None) -> dict:
    effective_mode = (mode or view_mode).lower()
    if effective_mode == "siloed":
        # Siloed / Manual uncoordinated plan
        siloed_blocks = [
            {
                "block_id": "BLK-2026-W36-004-ENG",
                "section_id": "HWH-BDC",
                "scheduled_start": "01:30",
                "scheduled_end": "04:30",
                "duration": 180,
                "departments_involved": ["Engineering"],
                "status": "ACTIVE",
                "priority": "High",
                "consolidated_tasks": [
                    {
                        "task_id": "TSK-1092",
                        "department": "Engineering",
                        "description": "Track renewal (Isolated)",
                        "severity": "IMR",
                        "allocated_time": 180,
                        "track_km_span": "Km 12-14",
                        "priority_score": 85.5,
                        "explainability": [{"feature": "IMR Severity Grade", "impact": 28.4}],
                    }
                ],
            },
            {
                "block_id": "BLK-2026-W36-004-SNT",
                "section_id": "HWH-BDC",
                "scheduled_start": "05:30",
                "scheduled_end": "07:30",
                "duration": 120,
                "departments_involved": ["Signal & Telecom"],
                "status": "PENDING_START",
                "priority": "Medium",
                "consolidated_tasks": [
                    {
                        "task_id": "TSK-1094",
                        "department": "Signal & Telecom",
                        "description": "Point Machine Testing",
                        "severity": "Normal",
                        "allocated_time": 120,
                        "track_km_span": "Km 13",
                        "priority_score": 62.0,
                        "explainability": [{"feature": "Safety Maintenance Interval", "impact": 18.0}],
                    }
                ],
            },
            {
                "block_id": "BLK-2026-W36-005",
                "section_id": "BDC-BWN",
                "scheduled_start": "10:00",
                "scheduled_end": "14:00",
                "duration": 240,
                "departments_involved": ["Electrical"],
                "status": "PENDING_START",
                "priority": "Medium",
                "consolidated_tasks": DATABASE["blocks"][1]["consolidated_tasks"],
            },
        ]
        siloed_kpis = [
            {"id": "kpi-1", "label": "Total Block Hours Saved", "value": "0.0 hrs", "unit": "hrs", "trend": "down", "trend_value": "Baseline uncoordinated", "status": "warning"},
            {"id": "kpi-2", "label": "Asset Availability", "value": "86.2", "unit": "%", "trend": "down", "trend_value": "-8.5% capacity loss", "status": "warning"},
            {"id": "kpi-3", "label": "Disruption Reduction", "value": "11.4", "unit": "%", "trend": "down", "trend_value": "High train regulation", "status": "warning"},
            {"id": "kpi-4", "label": "Active Conflicts", "value": "07", "unit": "", "trend": "up", "trend_value": "Overlapping demands", "status": "warning"},
        ]
        siloed_alerts = [
            *DATABASE["alerts"],
            {
                "id": "ALT-04",
                "type": "CONFLICT",
                "severity": "high",
                "title": "Dual Corridor Outage",
                "message": "Consecutive Engineering and S&T blocks will hold Up trains for > 4.5 cumulative hours.",
                "timestamp": "11:15",
            },
        ]
        return {
            "kpis": siloed_kpis,
            "blocks": siloed_blocks,
            "trains": DATABASE["trains"],
            "alerts": siloed_alerts,
            "corridors": DATABASE["corridors"],
            "view_mode": "siloed",
        }

    # Optimized View
    kpis = [
        {"id": "kpi-1", "label": "Total Block Hours Saved", "value": "18.5 hrs", "unit": "hrs", "trend": "up", "trend_value": "12.4% vs previous planning", "status": "good"},
        {"id": "kpi-2", "label": "Asset Availability", "value": "94.7", "unit": "%", "trend": "up", "trend_value": "2.1% from baseline", "status": "good"},
        {"id": "kpi-3", "label": "Disruption Reduction", "value": "37.2", "unit": "%", "trend": "down", "trend_value": "5% improvement", "status": "good"},
        {"id": "kpi-4", "label": "Active Conflicts", "value": "02" if any(b.get("decision") == "approved" for b in DATABASE["blocks"]) else "03", "unit": "", "trend": "neutral", "trend_value": "Under control", "status": "good" if any(b.get("decision") == "approved" for b in DATABASE["blocks"]) else "warning"},
    ]
    return {
        "kpis": kpis,
        "blocks": DATABASE["blocks"],
        "trains": DATABASE["trains"],
        "alerts": DATABASE["alerts"],
        "corridors": DATABASE["corridors"],
        "view_mode": "optimized",
    }


@app.post("/api/simulate")
def simulate(request: SimulationRequest) -> dict:
    target_block = next((b for b in DATABASE["blocks"] if b["block_id"] == request.block_id), None)
    
    # Calculate difference between current scheduled_end and new_end_time
    scheduled_end_min = parse_minutes(target_block["scheduled_end"]) if target_block else parse_minutes("05:00")
    new_end_min = parse_minutes(request.new_end_time)
    
    # Extension in minutes (can be negative if compressed, positive if extended)
    delta_minutes = new_end_min - scheduled_end_min

    if delta_minutes <= 0:
        return {
            "total_passenger_delay_minutes": 0,
            "regulated_freight_trains": 0,
            "punctuality_impact_pct": 0.0,
            "conflict_warnings": [
                f"No downstream delays predicted. Block {request.block_id} finishes on/before schedule.",
                "Line capacity clear for scheduled passenger priority slots.",
            ],
            "delta_minutes": delta_minutes,
        }

    # Dynamic calculation based on extension
    passenger_delay = int(delta_minutes * 0.75 + (delta_minutes // 30) * 8)
    freight_trains = max(1, delta_minutes // 20)
    punctuality_impact = -round(min(32.0, 2.0 + (delta_minutes / 15) * 1.6), 1)

    section = target_block["section_id"] if target_block else "Corridor"
    warnings = [
        f"Express 12303 held at outer signal (+{min(passenger_delay, 45)}m delay) on {section}",
    ]
    if delta_minutes >= 30:
        warnings.append(f"Freight 56821 regulated at {section.split('-')[0]} loop line for {delta_minutes} mins")
    if delta_minutes >= 60:
        warnings.append(f"Headway margin breached between {section} - Downstream cascade risk high")
    if delta_minutes >= 90:
        warnings.append("Mandatory COA division approval required: Extension exceeds 90-minute SLA threshold")

    return {
        "total_passenger_delay_minutes": passenger_delay,
        "regulated_freight_trains": freight_trains,
        "punctuality_impact_pct": punctuality_impact,
        "conflict_warnings": warnings,
        "delta_minutes": delta_minutes,
    }


@app.post("/api/blocks/{block_id}/decision")
def record_decision(block_id: str, request: DecisionRequest) -> dict:
    target_block = next((b for b in DATABASE["blocks"] if b["block_id"] == block_id), None)
    if not target_block:
        raise HTTPException(status_code=404, detail="Block not found")

    target_block["decision"] = request.decision
    target_block["decision_reason"] = request.reason
    target_block["decision_time"] = datetime.now().strftime("%H:%M")
    target_block["operator_role"] = request.operator_role

    if request.decision == "approved":
        target_block["status"] = "APPROVED"
        # Update or resolve conflict alert for this block
        for alert in DATABASE["alerts"]:
            if alert.get("related_block_id") == block_id:
                alert["type"] = "RESOLVED"
                alert["severity"] = "low"
                alert["message"] = f"Slot conflict resolved: Controller approved joint block {block_id}."
    else:
        target_block["status"] = "OVERRIDDEN"

    return {
        "message": f"Block {block_id} {request.decision.upper()} successfully",
        "block": target_block,
    }


@app.get("/api/telemetry")
@app.get("/api/telemetry/live")
def get_telemetry() -> list[dict]:
    # Returns real-time F-06 telemetry events
    now = datetime.now().strftime("%H:%M:%S")
    return [
        {
            "id": "TEL-01",
            "timestamp": now,
            "section": "HWH-BDC",
            "type": "TRACK_CIRCUIT",
            "status": "OCCUPIED",
            "detail": "Track Circuit TC-124 Active | Machine BCM-08 deployed at Km 13/4",
            "badge_color": "blue",
        },
        {
            "id": "TEL-02",
            "timestamp": now,
            "section": "HWH-BDC",
            "type": "TRACTION_POWER",
            "status": "ISOLATED",
            "detail": "25kV AC OHE switched off between Mst 12/10 - 14/02 | Earth discharge rods placed",
            "badge_color": "yellow",
        },
        {
            "id": "TEL-03",
            "timestamp": now,
            "section": "BDC-BWN",
            "type": "SIGNAL_ASPECT",
            "status": "NORMAL",
            "detail": "Automatic Block Signaling normal | Aspect: Caution for freight rake 56821",
            "badge_color": "green",
        },
        {
            "id": "TEL-04",
            "timestamp": now,
            "section": "HWH-BDC",
            "type": "SPEED_RESTRICTION",
            "status": "PSR_30",
            "detail": "Caution order 30 km/h notified on Down Line Km 12 to 14",
            "badge_color": "red",
        },
    ]


@app.get("/api/plan/export")
def export_plan() -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write metadata
    writer.writerow(["RailSync - Master Tactical Maintenance & Corridor Schedule"])
    writer.writerow(["Exported At", datetime.now().isoformat()])
    writer.writerow([])
    
    # Write Blocks
    writer.writerow(["Block ID", "Section", "Start Time", "End Time", "Duration (mins)", "Departments Involved", "Status", "Priority", "Decision", "Override Reason"])
    for b in DATABASE["blocks"]:
        writer.writerow([
            b["block_id"],
            b["section_id"],
            b["scheduled_start"],
            b["scheduled_end"],
            b["duration"],
            ", ".join(b["departments_involved"]),
            b["status"],
            b["priority"],
            b.get("decision", "PENDING"),
            b.get("decision_reason", ""),
        ])
    
    writer.writerow([])
    # Write Train Impact
    writer.writerow(["Train No", "Type", "Name", "Priority", "Scheduled Arrival", "Expected Arrival", "Predicted Delay (mins)"])
    for t in DATABASE["trains"]:
        writer.writerow([
            t["train_no"],
            t["train_type"],
            t["name"],
            t["priority"],
            t["scheduled_arrival"],
            t["expected_arrival"],
            t["delay_minutes"],
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="RailSync_Tactical_Plan.csv"'},
    )
