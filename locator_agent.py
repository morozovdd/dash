from uagents import Agent, Context, Model, Protocol
from typing import Dict, Optional
import aiohttp
import os
from shared_protocol import health_protocol, LocationData, emergency_protocol
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel

# Data models
class HospitalInfo(Model):
    name: str
    address: str
    distance: float
    travel_time: int  # in minutes

class LocationInfo(Model):
    address: str
    coordinates: LocationData
    nearest_hospital: HospitalInfo
    timestamp: str

class GeoInfo(Model):
    patient_address: str
    emergency_contact: str
    nearest_hospital: str
    estimated_travel_time: int
    coordinates: Dict[str, float]

# Create locator agent
locator_agent = Agent(
    name="locator-agent",
    seed="locator-agent-seed",
)

# Initialize API keys and endpoints on startup
@locator_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Locator agent starting up")
    ctx.logger.info(f"Agent address: {ctx.agent.address}")
    
    # Store API keys and endpoints
    ctx.storage.set('GOOGLE_MAPS_API_KEY', os.getenv('GOOGLE_MAPS_API_KEY'))
    ctx.storage.set('last_location_update', None)

async def get_address_from_coordinates(ctx: Context, lat: float, lon: float) -> str:
    """Get street address from coordinates using Google Maps Geocoding API"""
    api_key = ctx.storage.get('GOOGLE_MAPS_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data['status'] == 'OK':
                    return data['results'][0]['formatted_address']
                else:
                    ctx.logger.error(f"Geocoding API error: {data['status']}")
                    return "Address not found"
    except Exception as e:
        ctx.logger.error(f"Error getting address: {e}")
        return "Error getting address"

async def find_nearest_hospital(ctx: Context, lat: float, lon: float) -> HospitalInfo:
    """Find nearest hospital using Google Places API"""
    api_key = ctx.storage.get('GOOGLE_MAPS_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=5000&type=hospital&key={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data['status'] == 'OK' and data['results']:
                    hospital = data['results'][0]
                    
                    # Get travel time
                    travel_time = await get_travel_time(
                        ctx,
                        lat,
                        lon,
                        hospital['geometry']['location']['lat'],
                        hospital['geometry']['location']['lng']
                    )
                    
                    return HospitalInfo(
                        name=hospital['name'],
                        address=hospital['vicinity'],
                        distance=0.0,  # Could calculate if needed
                        travel_time=travel_time
                    )
                else:
                    ctx.logger.error(f"Places API error: {data['status']}")
                    return None
    except Exception as e:
        ctx.logger.error(f"Error finding hospital: {e}")
        return None

async def get_travel_time(ctx: Context, orig_lat: float, orig_lon: float, dest_lat: float, dest_lon: float) -> int:
    """Get estimated travel time in minutes using Google Distance Matrix API"""
    api_key = ctx.storage.get('GOOGLE_MAPS_API_KEY')
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={orig_lat},{orig_lon}&destinations={dest_lat},{dest_lon}&mode=driving&key={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if data['status'] == 'OK':
                    duration = data['rows'][0]['elements'][0]['duration']['value']
                    return int(duration / 60)  # Convert seconds to minutes
                else:
                    ctx.logger.error(f"Distance Matrix API error: {data['status']}")
                    return 0
    except Exception as e:
        ctx.logger.error(f"Error getting travel time: {e}")
        return 0

@health_protocol.on_message(model=LocationData)
async def handle_location_update(ctx: Context, sender: str, msg: LocationData):
    """Handle incoming location data and send geo information to decision maker"""
    ctx.logger.info(f"Received location update from {sender}")
    
    try:
        # Get address from coordinates
        address = await get_address_from_coordinates(ctx, msg.latitude, msg.longitude)
        
        # Find nearest hospital
        hospital_info = await find_nearest_hospital(ctx, msg.latitude, msg.longitude)
        
        if hospital_info:
            # Prepare geo information
            geo_info = GeoInfo(
                patient_address=address,
                emergency_contact="",  # Would be fetched from user profile
                nearest_hospital=hospital_info.name,
                estimated_travel_time=hospital_info.travel_time,
                coordinates={"latitude": msg.latitude, "longitude": msg.longitude}
            )
            
            # Send to decision maker
            DECISION_MAKER_ADDRESS = os.getenv("DECISION_MAKER_ADDRESS")
            await ctx.send(DECISION_MAKER_ADDRESS, geo_info)
            ctx.logger.info(f"Sent geo information to decision maker")
            
            # Update last location timestamp
            ctx.storage.set('last_location_update', datetime.now().isoformat())
        
    except Exception as e:
        ctx.logger.error(f"Error processing location update: {e}")

# Include the shared protocol
locator_agent.include(health_protocol)
locator_agent.include(emergency_protocol)