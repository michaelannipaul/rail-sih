import random
from datetime import datetime, timedelta
from enum import Enum

import httpx
from faker import Faker
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, field_validator, model_validator

app = FastAPI(title="Railway Data Normalization Service")
fake = Faker('en_IN')

# --- ENUMS ---
class Department(str, Enum):
    ENGINEERING = "ENGINEERING"
    SIGNAL_TELECOM = "SIGNAL_TELECOM"
    TRACTION = "TRACTION"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# --- Output Schemas ---
class UnifiedMaintenanceTask(BaseModel):
    id: str
    department: Department
    section_id: str
    start_km: float
    end_km: float
    base_severity: Severity
    estimated_duration_minutes: int
    due_date: datetime
    requires_power_block: bool
    requires_traffic_block: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "TASK-1001",
                "department": "ENGINEERING",
                "section_id": "SBC-MYS",
                "start_km": 10.5,
                "end_km": 12.0,
                "base_severity": "CRITICAL",
                "estimated_duration_minutes": 180,
                "due_date": "2026-09-10T12:00:00",
                "requires_power_block": False,
                "requires_traffic_block": True
            }
        }
    }

class WeatherAssessmentResult(BaseModel):
    viable: bool
    risk_multiplier: float
    warning_reasons: list[str]
    mapped_location: dict[str, float]

# --- Dynamic Mock Database for Railway Section Coordinates ---
SECTION_COORDINATES: dict[str, dict[str, float]] = {
    "SBC-MYS": {"lat": 12.9716, "lon": 77.5946},
    "HWH-BWN-CHORD-UP": {"lat": 22.5726, "lon": 88.3639},
    "SDAH-KLYM-UP": {"lat": 22.9747, "lon": 88.4337},
    # Common IR sections for testing & mock data integration
    "NDLS-CNB": {"lat": 28.6139, "lon": 77.2090},
    "BCT-ST": {"lat": 18.9696, "lon": 72.8193},
    "MAS-BZA": {"lat": 13.0827, "lon": 80.2707},
    "HWH-KGP": {"lat": 22.5839, "lon": 88.3433},
    "CSTM-Kalyan": {"lat": 18.9401, "lon": 72.8347},
    "HWH-BWN": {"lat": 22.5839, "lon": 88.3433},
}

# --- Input Schemas ---

class TMSDefect(BaseModel):
    ticket_id: str
    track_id: str
    km_start: float | str
    km_end: float | str
    defect_class: str
    date_detected: datetime
    speed_restriction_applied: bool

    @field_validator('km_start', 'km_end', mode='before')
    @classmethod
    def validate_km(cls, v):
        try:
            val = float(v)
            if val < 0:
                return 0.0 # Handle malformed negative km
            return val
        except (ValueError, TypeError):
            # Fallback for malformed or missing strings
            return 0.0
            
    @model_validator(mode='after')
    def check_km_order(self):
        if float(self.km_start) > float(self.km_end):
            self.km_start, self.km_end = self.km_end, self.km_start
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticket_id": "TMS-4819201",
                "track_id": "NDLS-CNB",
                "km_start": 12.4,
                "km_end": 14.1,
                "defect_class": "IMR",
                "date_detected": "2026-09-05T10:00:00",
                "speed_restriction_applied": True
            }
        }
    }

class SMMSFault(BaseModel):
    fault_id: str
    station_code: str
    gear_type: str
    failure_category: str
    reported_ts: datetime
    urgency_code: str # e.g., 'U1' (Critical), 'U2'

    model_config = {
        "json_schema_extra": {
            "example": {
                "fault_id": "SMMS-7821903",
                "station_code": "NDLS",
                "gear_type": "Point Machine",
                "failure_category": "EQUIPMENT_FAILURE",
                "reported_ts": "2026-09-05T11:30:00",
                "urgency_code": "U1"
            }
        }
    }

class TDMSDefect(BaseModel):
    defect_no: str
    ohe_substation: str
    mast_from: str # e.g. "120/15" -> km 120.15
    mast_to: str
    issue_type: str
    scheduled_date: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "defect_no": "TDMS-9182304",
                "ohe_substation": "TSS-NDLS",
                "mast_from": "120/15",
                "mast_to": "120/35",
                "issue_type": "CONTACT WIRE WEAR",
                "scheduled_date": "2026-09-06T09:00:00"
            }
        }
    }

# --- Parsers ---

def parse_tms(defect: TMSDefect) -> UnifiedMaintenanceTask:
    severity_map = {
        "IMR": Severity.CRITICAL,
        "OBS": Severity.HIGH,
        "WELD_DEFECT": Severity.MEDIUM,
        "MINOR_CRACK": Severity.LOW
    }
    # Default to LOW if not found
    severity = severity_map.get(defect.defect_class.strip().upper(), Severity.LOW)
    
    return UnifiedMaintenanceTask(
        id=defect.ticket_id,
        department=Department.ENGINEERING,
        section_id=defect.track_id,
        start_km=float(defect.km_start),
        end_km=float(defect.km_end),
        base_severity=severity,
        estimated_duration_minutes=240 if severity == Severity.CRITICAL else 120,
        due_date=defect.date_detected + timedelta(days=1 if severity == Severity.CRITICAL else 7),
        requires_power_block=(severity == Severity.CRITICAL), # High-risk track works need power block
        requires_traffic_block=defect.speed_restriction_applied or severity in (Severity.CRITICAL, Severity.HIGH)
    )

def parse_smms(fault: SMMSFault) -> UnifiedMaintenanceTask:
    severity_map = {
        "U1": Severity.CRITICAL,
        "U2": Severity.HIGH,
        "U3": Severity.MEDIUM,
        "U4": Severity.LOW
    }
    severity = severity_map.get(fault.urgency_code.strip().upper(), Severity.LOW)
    
    return UnifiedMaintenanceTask(
        id=fault.fault_id,
        department=Department.SIGNAL_TELECOM,
        section_id=fault.station_code,
        start_km=0.0, # SMMS is station based usually, discrete location
        end_km=0.0,
        base_severity=severity,
        estimated_duration_minutes=180 if severity in (Severity.CRITICAL, Severity.HIGH) else 60,
        due_date=fault.reported_ts + timedelta(hours=4 if severity == Severity.CRITICAL else 24),
        requires_power_block=False,
        requires_traffic_block=(fault.gear_type.lower() == "point machine")
    )

def _parse_mast(mast_str: str) -> float:
    try:
        parts = mast_str.split('/')
        if len(parts) == 2:
            return float(parts[0]) + float(parts[1]) / 100.0
        return float(mast_str)
    except (ValueError, TypeError, IndexError):
        return 0.0

def parse_tdms(defect: TDMSDefect) -> UnifiedMaintenanceTask:
    severity_map = {
        "CONTACT_WIRE_WEAR": Severity.CRITICAL,
        "CANTILEVER_REPLACEMENT": Severity.HIGH,
        "INSULATOR_CLEANING": Severity.MEDIUM,
    }
    issue = defect.issue_type.strip().upper().replace(" ", "_")
    severity = severity_map.get(issue, Severity.LOW)
    
    start_km = _parse_mast(defect.mast_from)
    end_km = _parse_mast(defect.mast_to)
    if start_km > end_km:
        start_km, end_km = end_km, start_km
        
    return UnifiedMaintenanceTask(
        id=defect.defect_no,
        department=Department.TRACTION,
        section_id=defect.ohe_substation,
        start_km=start_km,
        end_km=end_km,
        base_severity=severity,
        estimated_duration_minutes=120,
        due_date=defect.scheduled_date,
        requires_power_block=True, # Always true for traction work
        requires_traffic_block=True # Overhead work usually blocks traffic
    )

# --- FastAPI Endpoints ---

@app.get("/", include_in_schema=False)
def root():
    """Redirect root directly to interactive Swagger UI documentation."""
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Eliminates 404 Not Found logs in terminal caused by browser favicon requests."""
    return Response(status_code=204)

@app.get("/api-info")
def api_info():
    return {
        "status": "online",
        "service": "Railway Data Normalization Service",
        "endpoints": {
            "docs": "/docs",
            "mock_data": "/mock-data",
            "normalize_tms": "/normalize/tms (POST)",
            "normalize_smms": "/normalize/smms (POST)",
            "normalize_tdms": "/normalize/tdms (POST)",
            "normalize_weather_risk": "/normalize/weather-risk (POST)"
        }
    }

@app.post("/normalize/tms", response_model=UnifiedMaintenanceTask)
def normalize_tms_endpoint(defect: TMSDefect):
    return parse_tms(defect)

@app.post("/normalize/smms", response_model=UnifiedMaintenanceTask)
def normalize_smms_endpoint(fault: SMMSFault):
    return parse_smms(fault)

@app.post("/normalize/tdms", response_model=UnifiedMaintenanceTask)
def normalize_tdms_endpoint(defect: TDMSDefect):
    return parse_tdms(defect)

# --- Weather & Environmental Risk Engine ---

def evaluate_weather_rules(
    department: Department | str,
    requires_traffic_block: bool,
    temperature: float,
    wind_speed: float,
    visibility: float,
    rain: float
) -> tuple[bool, float, list[str]]:
    viable = True
    risk_multiplier = 1.0
    warning_reasons: list[str] = []

    # Rule A: If task.department == "ENGINEERING" and temperature > 42.0°C
    if (department == Department.ENGINEERING or department == "ENGINEERING") and temperature > 42.0:
        viable = False
        warning_reasons.append("Temperature exceeds safety limit. Track buckling risk.")

    # Rule B: If task.department == "TRACTION" and wind_speed > 50.0 km/h
    if (department == Department.TRACTION or department == "TRACTION") and wind_speed > 50.0:
        viable = False
        warning_reasons.append("High crosswinds. OHE ladder work unsafe.")

    # Rule C: If visibility < 300 meters and task.requires_traffic_block is True
    if visibility < 300.0 and requires_traffic_block:
        risk_multiplier += 0.35
        warning_reasons.append("Fog advisory. Increased signal headway required.")

    # Rule D: If rain > 2.0 mm
    if rain > 2.0:
        risk_multiplier += 0.2
        warning_reasons.append("Active rainfall. Ground slip hazard.")

    return viable, round(risk_multiplier, 2), warning_reasons

@app.post("/normalize/weather-risk", response_model=WeatherAssessmentResult)
async def normalize_weather_risk(task: UnifiedMaintenanceTask):
    coords = SECTION_COORDINATES.get(task.section_id)
    if not coords:
        raise HTTPException(status_code=404, detail="Coordinates for section not found.")

    lat = coords["lat"]
    lon = coords["lon"]
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current=temperature_2m,rain,wind_speed_10m,visibility"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            weather_data = response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch weather data: {exc!s}")

    current = weather_data.get("current", {})
    temperature = current.get("temperature_2m", 0.0)
    rain = current.get("rain", 0.0)
    wind_speed = current.get("wind_speed_10m", 0.0)
    visibility = current.get("visibility", 10000.0)

    viable, risk_multiplier, warning_reasons = evaluate_weather_rules(
        department=task.department,
        requires_traffic_block=task.requires_traffic_block,
        temperature=temperature,
        wind_speed=wind_speed,
        visibility=visibility,
        rain=rain
    )

    return WeatherAssessmentResult(
        viable=viable,
        risk_multiplier=risk_multiplier,
        warning_reasons=warning_reasons,
        mapped_location={"lat": lat, "lon": lon}
    )

@app.get("/mock-data")
def get_mock_data():
    """Generates 100 sample records per department with realistic Indian Railways sections."""
    ir_sections = ["NDLS-CNB", "BCT-ST", "MAS-BZA", "HWH-KGP", "SBC-MYS", "CSTM-Kalyan", "HWH-BWN"]
    station_codes = ["NDLS", "CNB", "BCT", "ST", "MAS", "BZA", "HWH", "KGP", "SBC", "MYS", "CSTM", "BWN"]
    tms_defects = ["IMR", "OBS", "WELD_DEFECT", "MINOR_CRACK"]
    smms_gears = ["Point Machine", "Track Circuit", "Signal Lamp"]
    smms_urgencies = ["U1", "U2", "U3", "U4"]
    tdms_issues = ["CONTACT WIRE WEAR", "CANTILEVER REPLACEMENT", "INSULATOR CLEANING", "BIRD NEST"]

    mock_tms = []
    mock_smms = []
    mock_tdms = []

    for _ in range(100):
        # 1. Engineering / TMS
        start = round(random.uniform(0, 500), 2)
        end = round(start + random.uniform(0.1, 2.0), 2)
        
        # Sometimes inject a malformed coordinate
        km_start_val = start if random.random() > 0.05 else "N/A"
        
        mock_tms.append(
            TMSDefect(
                ticket_id=f"TMS-{fake.unique.random_number(digits=7)}",
                track_id=random.choice(ir_sections),
                km_start=km_start_val,
                km_end=end,
                defect_class=random.choice(tms_defects),
                date_detected=fake.date_time_between(start_date="-30d", end_date="now"),
                speed_restriction_applied=random.choice([True, False])
            ).model_dump(mode="json")
        )

        # 2. Signalling / SMMS
        mock_smms.append(
            SMMSFault(
                fault_id=f"SMMS-{fake.unique.random_number(digits=7)}",
                station_code=random.choice(station_codes),
                gear_type=random.choice(smms_gears),
                failure_category="EQUIPMENT_FAILURE",
                reported_ts=fake.date_time_between(start_date="-10d", end_date="now"),
                urgency_code=random.choice(smms_urgencies)
            ).model_dump(mode="json")
        )

        # 3. Traction / TDMS
        base_mast = random.randint(10, 500)
        # Handle mast from and to logic (mast '120/15' means km 120.15)
        mock_tdms.append(
            TDMSDefect(
                defect_no=f"TDMS-{fake.unique.random_number(digits=7)}",
                ohe_substation=f"TSS-{random.choice(station_codes)}",
                mast_from=f"{base_mast}/{random.randint(1, 30)}",
                mast_to=f"{base_mast}/{random.randint(31, 60)}",
                issue_type=random.choice(tdms_issues),
                scheduled_date=fake.date_time_between(start_date="now", end_date="+15d")
            ).model_dump(mode="json")
        )
        
    return {
        "TMS_Engineering": mock_tms,
        "SMMS_Signal_Telecom": mock_smms,
        "TDMS_Traction": mock_tdms
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)

