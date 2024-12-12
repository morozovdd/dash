from typing import Any, Dict, List, Optional
from uagents import Model
import requests
import os
from uagents import Agent, Context

class Coordinates(Model):
    latitude: float
    longitude: float

class POIAreaRequest(Model):
    loc_search: Coordinates
    radius_in_m: int
    limit: int = 20
    query_string: str
    filter: Dict[str, Any] = {}

class Result(Model):
    userLocation: dict
    hospitalLocation: dict
    traffic_distance: str 
    traffic_duration: str
    msg: str

class POI(Model):
    placekey: str
    location_name: str
    brands: Optional[List[str]] = None
    top_category: Optional[str] = None
    sub_category: Optional[str] = None
    location: Coordinates
    address: str
    city: str
    region: Optional[str] = None
    postal_code: str
    iso_country_code: str
    metadata: Optional[Dict[str, Any]] = None

class POIResponse(Model):
    loc_search: Coordinates
    radius_in_m: int
    data_origin: str
    data: List[POI]
    
locator_agent = Agent(
    name="locator_agent",
    seed="locator_agent_seed",
)

COLLECTOR_ADDRESS = os.getenv("COLLECTOR_ADDRESS")
GMAPS_AGENT_ADDRESS = "agent1qvcqsyxsq7fpy9z2r0quvng5xnhhwn3vy7tmn5v0zwr4nlm7hcqrckcny9e"

def reverse_geocode(lat, lon):
    api_key = GOOGLE_MAP_API
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        if result["results"]:
            return result["results"][0]
        else:
            return "No address found"
    else:
        return f"Error: {response.status_code}"

def check_traffic_conditions(origin: Tuple[float, float], destination: Tuple[float, float]):
    api_key = GOOGLE_MAP_API
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin[0]},{origin[1]}"
        f"&destination={destination[0]},{destination[1]}"
        f"&departure_time=now"  # Enables real-time traffic data
        f"&key={api_key}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            legs = data["routes"][0]["legs"][0]
            print(legs)
            distance = legs["distance"]["text"]
            duration = legs["duration"]["text"]
            
            # traffic_dist = legs.get("duration_in_traffic", {}).get("text", "Unknown")
            return {"dist": distance, "dura": duration}
        else:
            return f"Error: {data['status']}"
    else:
        return f"Error: {response.status_code}"


@agent.on_message(Coordinates)
async def handle_sending_coordinates(ctx: Context, sender: str, msg: Coordinates):
    request = POIAreaRequest(loc_search=msg, 
                            radius_in_m=2000, 
                            limit=5, query_string="hospital")

    await ctx.send(GMAPS_AGENT_ADDRESS, request)
    ctx.logger.info(f"Sent coordinates {msg} to agent {GMAPS_AGENT_ADDRESS}")

@agent.on_message(POIResponse)
async def handle_poi_response(ctx: Context, sender: str, msg: POIResponse):
    # Get user location's address
    user_address = reverse_geocode(msg.loc_search.latitude, msg.loc_search.longitude)
    
    ctx.logger.info(f"User address: {user_address}")

    # Find the nearest hospital
    if not msg.data:
        ctx.logger.warning("No hospitals found in POIResponse")
        return

    nearest_hospital = msg.data[0]  # Assuming the first POI is the nearest
    hospital_address = nearest_hospital.address
    hospital_name = nearest_hospital.location_name
    ctx.logger.info(f"Nearest hospital: {hospital_name}, Address: {hospital_address}")

    traffic_condition = check_traffic_conditions([msg.loc_search.latitude, msg.loc_search.longitude],[nearest_hospital.location.latitude,nearest_hospital.location.longitude])
    
    ctx.logger.info(f"{traffic_condition}")
    # Prepare the final message
    result = Result(userLocation = {
            "latitude": msg.loc_search.latitude,
            "longitude": msg.loc_search.longitude,
            "address": user_address['formatted_address'],
        },
        hospitalLocation = {
            "latitude": nearest_hospital.location.latitude,
            "longitude": nearest_hospital.location.longitude,
            "name": hospital_name,
            "address": hospital_address,
        }, traffic_distance = traffic_condition['dist'], traffic_duration = traffic_condition['dura'], msg=f"Your current location is {user_address['formatted_address']}. Nearest Hospital is {hospital_address}.")
        
    ctx.logger.info(f"{result}")

    ctx.logger.info(f"Sent user and hospital locations to receiver {receiver}")
    if receiver == "":
        await ctx.send(receiver, result)