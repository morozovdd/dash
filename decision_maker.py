from uagents import Agent, Context, Model, Protocol
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

# Message models
class AccidentAnalysis(Model):
    alert: bool
    context: str

class GeoInfo(Model):
    patient_address: str  # Full address of the patient
    emergency_contact: str  # Phone or contact info
    nearest_hospital: str  # Name/address of nearest hospital
    estimated_travel_time: int  # minutes to reach patient
    coordinates: Dict[str, float]  # {"latitude": x, "longitude": y}

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

class UserNotification(Model):
    timestamp: str
    alert_type: str
    message: str
    requires_response: bool

# Create protocols
emergency_protocol = Protocol("emergency-decision", "0.1.0")

# Constants
ALERT_THRESHOLD_TIME = 300  # 5 minutes in seconds
USER_RESPONSE_TIMEOUT = 300  # 5 minutes in seconds
EMERGENCY_SERVICE_ADDRESS = "emergency_service_address_here"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_CHAT_ID = os.getenv("USER_CHAT_ID")
EMERGENCY_CONTACT_CHAT_ID = os.getenv("EMERGENCY_CONTACT_CHAT_ID")
LLMCOMMUNICATOR_ADDRESS = os.getenv("LLMCOMMUNICATOR_ADDRESS")

# Create decision maker agent
decision_maker = Agent(name="decision-maker",
                       seed="decision-maker-seed",                      
                        )

# Store for tracking alert states
@decision_maker.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Decision maker agent starting up")
    ctx.logger.info(f"Agent address: {ctx.agent.address}")
    ctx.storage.set('alert_status', {
        'first_alert_time': None,
        'consecutive_alerts': 0,
        'user_notified': False,
        'user_responded': False,
    })

# Handle incoming accident analysis
@emergency_protocol.on_message(model=AccidentAnalysis)
async def handle_analysis(ctx: Context, sender: str, msg: AccidentAnalysis):
    ctx.logger.info(f"Received analysis from {sender}: Alert={msg.alert}")
    
    status = ctx.storage.get('alert_status')
    current_time = datetime.now()
    
    if msg.alert:
        if status['first_alert_time'] is None:
            # Store datetime as ISO format string
            status['first_alert_time'] = current_time.isoformat()
        
        status['consecutive_alerts'] += 1
        
        # If we haven't notified user yet and have multiple alerts
        if not status['user_notified'] and status['consecutive_alerts'] >= 2:
            await notify_user(ctx)
            status['user_notified'] = True
        
        # Check if conditions for emergency services are met
        if should_contact_emergency(status):
            await notify_emergency_services(ctx, msg.context)
            
    else:
        # Reset alert status if no alert
        status = {
            'first_alert_time': None,
            'consecutive_alerts': 0,
            'user_notified': False,
            'user_responded': False,
        }
    
    ctx.storage.set('alert_status', status)

# Handle geolocation updates
@emergency_protocol.on_message(model=GeoInfo)
async def handle_traffic(ctx: Context, sender: str, msg: GeoInfo):
    status = ctx.storage.get('alert_status')
    status['traffic_status'] = msg.traffic_level
    ctx.storage.set('alert_status', status)
    
# Handle user responses
@emergency_protocol.on_message(model=UserResponse)
async def handle_user_response(ctx: Context, sender: str, msg: UserResponse):
    status = ctx.storage.get('alert_status')
    status['user_responded'] = msg.responded
    ctx.storage.set('alert_status', status)

async def notify_user(ctx: Context):
    """Send Telegram notification to user with response buttons"""
    keyboard = [
        [
            InlineKeyboardButton("I'm OK", callback_data='ok'),
            InlineKeyboardButton("Need Help", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Send alert message with buttons
        await app.bot.send_message(
            chat_id=USER_CHAT_ID,
            text="🚨 Possible emergency detected! Are you OK?",
            reply_markup=reply_markup
        )
        
        # Handle button responses
        async def button_callback(update: Update, _: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            
            response = UserResponse(
                responded=True,
                response_time=datetime.now(),
                is_ok=query.data == 'ok'
            )
            
            # Update the message to show response received
            await query.edit_message_text(
                text=f"Response received: {'OK' if query.data == 'ok' else 'Help needed'}"
            )
            
            # Send response back to our agent system
            await ctx.send(ctx.address, response)
        
        app.add_handler(CallbackQueryHandler(button_callback))
        await app.initialize()
        await app.start()
        
        ctx.logger.info("Telegram notification sent with response buttons")
        
    except Exception as e:
        ctx.logger.error(f"Failed to send Telegram notification: {e}")

async def notify_emergency_services(ctx: Context, context: str):
    """Send notification to emergency services and emergency contact"""
    geo_info = ctx.storage.get('geo_info')  # Store from latest GeoInfo update
    
    if not geo_info:
        ctx.logger.error("No location information available!")
        return
    
    # Prepare emergency notification
    notification = EmergencyNotification(
        timestamp=datetime.now().isoformat(),
        location=geo_info.patient_address,
        patient_id="USER_ID_HERE",
        vital_signs={},  # This would be filled with actual vital signs
        context=context,
        nearest_hospital=geo_info.nearest_hospital,
        estimated_arrival=geo_info.estimated_travel_time
    )
    
    try:
        # Send to emergency services
        await ctx.send(EMERGENCY_SERVICE_ADDRESS, notification)
        ctx.logger.warning("🚨 Emergency services notified!")
        
        # Send Telegram alert to emergency contact
        emergency_message = (
            f"🚨 EMERGENCY ALERT!\n\n"
            f"Your emergency contact may need assistance.\n"
            f"Location: {geo_info.patient_address}\n"
            f"Nearest Hospital: {geo_info.nearest_hospital}\n"
            f"ETA to location: {geo_info.estimated_travel_time} minutes\n\n"
            f"Emergency services have been notified."
        )
        
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(
            chat_id=EMERGENCY_CONTACT_CHAT_ID,  # Need to add this to environment variables
            text=emergency_message
        )
        
        # Reset alert status after notifications
        status = ctx.storage.get('alert_status')
        status.update({
            'first_alert_time': None,
            'consecutive_alerts': 0,
            'user_notified': False,
            'user_responded': False,
        })
        ctx.storage.set('alert_status', status)
        
    except Exception as e:
        ctx.logger.error(f"Failed to send emergency notifications: {e}")

def should_contact_emergency(status: dict) -> bool:
    """Determine if emergency services should be contacted"""
    if not status['first_alert_time']:
        return False
    
    try:
        # Convert stored ISO format string back to datetime
        first_alert_time = datetime.fromisoformat(status['first_alert_time'])
        time_difference = (datetime.now() - first_alert_time).total_seconds()
    except (TypeError, ValueError):
        return False
        
    conditions = [
        # Alert has been active for threshold time
        time_difference >= ALERT_THRESHOLD_TIME,
        
        # Have multiple consecutive alerts
        status['consecutive_alerts'] >= 3,
        
        # User was notified but hasn't responded in time
        status['user_notified'] and not status['user_responded']
    ]
    
    return all(conditions)

# Include protocol
decision_maker.include(emergency_protocol)

if __name__ == "__main__":
    decision_maker.run()