from uagents import Model, Protocol
from typing import List, Dict

# Shared data models
class LocationData(Model):
    latitude: float
    longitude: float

class HospitalInfo(Model):
    name: str
    address: str
    distance: float
    travel_time: int

class GeoInfo(Model):
    patient_address: str
    emergency_contact: str
    nearest_hospital: str
    estimated_travel_time: int
    coordinates: Dict[str, float]

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

# Create shared protocol
health_protocol = Protocol("health-monitoring", "0.1.0")
emergency_protocol = Protocol("emergency-decision", "0.1.0")

# Define message paths in protocol
@health_protocol.on_message(model=AggregatedHealthData, replies=AccidentAnalysis)
def health_data_handler():
    """Handle health data messages"""
    pass

@health_protocol.on_message(model=LocationData, replies=GeoInfo)
def location_handler():
    """Handle location data messages"""
    pass

@emergency_protocol.on_message(model=GeoInfo)
def geo_info_handler():
    """Handle geo information messages"""
    pass

@emergency_protocol.on_message(model=AccidentAnalysis)
def analysis_handler():
    """Handle accident analysis messages"""
    pass