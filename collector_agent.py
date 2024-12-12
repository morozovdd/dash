from uagents import Agent, Context, Model
import aiohttp
from datetime import datetime
from typing import List, Dict
import json
from pydantic import BaseModel
import requests
from shared_protocol import health_protocol, AggregatedHealthData
import os
from shared_protocol import LocationData

# Define data models
class VitalSigns(Model):
    heart_rate: float
    spo2: float
    respiratory_rate: float
    systolic: int
    diastolic: int

class MovementData(Model):
    x: float
    y: float
    z: float
    device_orientation: str
    activity_state: str
    minutes_since_last_movement: float

class ContextData(Model):
    location_type: str
    time_of_day: str
    gps_coordinates: LocationData

class HealthData(Model):
    timestamp: str
    user_id: str
    vital_signs: VitalSigns
    movement_data: MovementData
    context: ContextData

# Create agent
collector_agent = Agent(
    name="health-monitoring-agent",
    seed="health-monitoring-agent-seed",
)

# Initialize storage on startup
@collector_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Starting up health monitoring agent")
    ctx.logger.info(f"Agent address: {ctx.agent.address}")
    ctx.storage.set('data_points', [])
    ctx.storage.set('last_aggregation', datetime.now().timestamp())

# Cleanup on shutdown
@collector_agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Health monitoring agent shutting down")
    # Aggregate any remaining data before shutdown
    await aggregate_and_send_data(ctx)

# Fetch health data every 10 seconds
@collector_agent.on_interval(period=5.0)
async def fetch_health_data(ctx: Context):
    url = "https://53a4-162-254-52-15.ngrok-free.app/health/user123"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            data_points = ctx.storage.get('data_points') or []
            ctx.logger.info("Received data point")
            data_points.append(data)
            ctx.storage.set('data_points', data_points)
            
            # Check if we have collected 5 data points
            if len(data_points) >= 5:
                await aggregate_and_send_data(ctx)
                # Reset storage
                ctx.storage.set('data_points', [])
        else:
            ctx.logger.error(f"Failed to fetch health data: {response.status_code}")
    except Exception as e:
        ctx.logger.error(f"Error fetching health data: {e}")

async def aggregate_and_send_data(ctx: Context):
    data_points = ctx.storage.get('data_points')
    if not data_points:
        return
    
    # Initialize aggregated data structure for analyzer
    aggregated = {
        'timestamps': [],
        'user_id': data_points[0]['user_id'],
        'vital_signs': {
            'heart_rate': [],
            'spo2': [],
            'respiratory_rate': []
        },
        'blood_pressure': {
            'systolic': [],
            'diastolic': []
        },
        'movement_data': {
            'x': [],
            'y': [],
            'z': [],
            'minutes_since_last_movement': []
        },
        'device_states': {
            'device_orientation': [],
            'activity_state': []
        },
        'context': {
            'location_type': [],
            'time_of_day': []
        },
        'gps_coordinates': {
            'latitude': [],
            'longitude': []
        }
    }
    
    # Aggregate data
    for point in data_points:
        aggregated['timestamps'].append(point['timestamp'])
        
        # Vital signs
        vital_signs = point['vital_signs']
        aggregated['vital_signs']['heart_rate'].append(vital_signs['heart_rate'])
        aggregated['vital_signs']['spo2'].append(vital_signs['spo2'])
        aggregated['vital_signs']['respiratory_rate'].append(vital_signs['respiratory_rate'])
        
        # Blood pressure
        aggregated['blood_pressure']['systolic'].append(vital_signs['blood_pressure']['systolic'])
        aggregated['blood_pressure']['diastolic'].append(vital_signs['blood_pressure']['diastolic'])
        
        # Movement data
        movement = point['movement_data']
        aggregated['movement_data']['x'].append(movement['acceleration']['x'])
        aggregated['movement_data']['y'].append(movement['acceleration']['y'])
        aggregated['movement_data']['z'].append(movement['acceleration']['z'])
        aggregated['movement_data']['minutes_since_last_movement'].append(movement['minutes_since_last_movement'])
        
        # Device states
        aggregated['device_states']['device_orientation'].append(movement['device_orientation'])
        aggregated['device_states']['activity_state'].append(movement['activity_state'])
        
        # Context
        context = point['context']
        aggregated['context']['location_type'].append(context['location_type'])
        aggregated['context']['time_of_day'].append(context['time_of_day'])
        aggregated['gps_coordinates']['latitude'].append(context['gps_coordinates']['latitude'])
        aggregated['gps_coordinates']['longitude'].append(context['gps_coordinates']['longitude'])
    
    # Log aggregated data
    ctx.logger.info(f"Aggregated health data:")
    ctx.logger.info(json.dumps(aggregated, indent=2))

    # Send the data to another agent
    try:
        health_data = AggregatedHealthData(**aggregated)
        ANALYZER_ADDRESS = os.getenv("ANALYZER_ADDRESS")
        await ctx.send(ANALYZER_ADDRESS, health_data)
        ctx.logger.info(f"Sent aggregated data via health protocol")
    except Exception as e:
        ctx.logger.error(f"Error sending data: {e}")

# Include the shared protocol
collector_agent.include(health_protocol)