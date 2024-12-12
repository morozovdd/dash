from uagents import Model, Protocol
from typing import List, Dict
from datetime import datetime

# Health Data Models
class AggregatedHealthData(Model):
    timestamps: List[str]
    user_id: str
    vital_signs: Dict[str, List[float]]
    blood_pressure: Dict[str, List[int]]
    movement_data: Dict[str, List[float]]
    device_states: Dict[str, List[str]]
    context: Dict[str, List[str]]
    gps_coordinates: Dict[str, List[float]]

class AccidentAnalysis(Model):
    alert: bool
    context: str

class LocationData(Model):
    latitude: float
    longitude: float

# Emergency Models
class GeoInfo(Model):
    patient_address: str
    emergency_contact: str
    nearest_hospital: str
    estimated_travel_time: int
    coordinates: Dict[str, float]

class UserResponse(Model):
    responded: bool
    response_time: datetime

class EmergencyNotification(Model):
    timestamp: str
    location: str
    patient_id: str
    vital_signs: Dict
    context: str
    nearest_hospital: str
    estimated_arrival: int

# Create shared protocols
health_protocol = Protocol("health-analysis", "0.1.0")
emergency_protocol = Protocol("emergency-decision", "0.1.0")