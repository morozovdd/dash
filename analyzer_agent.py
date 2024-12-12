from uagents import Agent, Context, Model, Protocol
import google.generativeai as genai
from typing import List, Dict
import json
import os
from shared_protocol import health_protocol, AggregatedHealthData, AccidentAnalysis


# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash-001')


class AccidentAnalysis(Model):
    alert: bool
    context: str

# Create analyzer agent
analyzer_agent = Agent(
    name="llm_communicator",
    seed="llm_communicator_seed",
)

@analyzer_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Health analyzer agent starting up")
    ctx.logger.info(f"Agent address: {ctx.agent.address}")

@health_protocol.on_message(model=AggregatedHealthData, replies=AccidentAnalysis)
async def analyze_health_data(ctx: Context, sender: str, msg: AggregatedHealthData):
    ctx.logger.info(f"Received health data from {sender}")
    
    # Prepare data for analysis
    analysis_prompt = f"""
    Analyze this health data and determine if there might be an accident or emergency situation:
    
    Time period: {msg.timestamps[0]} to {msg.timestamps[-1]}
    
    Vital Signs Summary:
    - Heart Rate (avg): {sum(msg.vital_signs['heart_rate']) / len(msg.vital_signs['heart_rate']):.1f} bpm
    - SpO2 (avg): {sum(msg.vital_signs['spo2']) / len(msg.vital_signs['spo2']):.1f}%
    - Respiratory Rate (avg): {sum(msg.vital_signs['respiratory_rate']) / len(msg.vital_signs['respiratory_rate']):.1f}
    - Blood Pressure: 
        Systolic (avg): {sum(msg.blood_pressure['systolic']) / len(msg.blood_pressure['systolic']):.1f}
        Diastolic (avg): {sum(msg.blood_pressure['diastolic']) / len(msg.blood_pressure['diastolic']):.1f}
    
    Movement Patterns:
    - Activity States: {set(msg.device_states['activity_state'])}
    - Minutes Since Last Movement (avg): {sum(msg.movement_data['minutes_since_last_movement']) / len(msg.movement_data['minutes_since_last_movement']):.1f}
    
    Acceleration:
    - X: {msg.movement_data['x']}
    - Y: {msg.movement_data['y']}
    - Z: {msg.movement_data['z']}
    
    Context:
    - Location Types: {set(msg.context['location_type'])}
    - Times of Day: {set(msg.context['time_of_day'])}
    
    Please analyze if there might be an accident or emergency situation. Respond in the following format only:
    ALERT: true/false
    REASON: detailed explanation of why an alert is or isn't needed
    """
    
    try:
        # Get analysis from Gemini
        response = model.generate_content(analysis_prompt)
        analysis_text = response.text
        
        # Parse the response
        lines = analysis_text.split('\n')
        alert = False
        context = "Analysis failed"
        
        for line in lines:
            if line.startswith('ALERT:'):
                alert = 'true' in line.lower()
            elif line.startswith('REASON:'):
                context = line.replace('REASON:', '').strip()
        
        try:
            # After analysis, send to decision maker
            analysis = AccidentAnalysis(
                alert=alert,
                context=context
            )
            
            # Get decision maker address from environment or configuration
            DECISION_MAKER_ADDRESS = os.getenv("DECISION_MAKER_ADDRESS")
            await ctx.send(DECISION_MAKER_ADDRESS, analysis)
            ctx.logger.info(f"Sent analysis to decision maker")
                
        except Exception as e:
            ctx.logger.error(f"Error sending analysis to decision maker: {e}")
        
        # Log the analysis
        if alert:
            ctx.logger.warning(f"⚠️ ACCIDENT ALERT: {context}")
        else:
            ctx.logger.info(f"No accident detected: {context}")
        
    except Exception as e:
        ctx.logger.error(f"Error analyzing health data: {e}")
        await ctx.send(
            sender,
            AccidentAnalysis(
                alert=False,
                context=f"Error analyzing data: {str(e)}"
            )
        )

# Include the shared protocol
analyzer_agent.include(health_protocol)