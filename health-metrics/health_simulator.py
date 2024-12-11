from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import math
import time
from typing import Dict, List, Optional

class HealthMetrics:
    def __init__(self, user_id: str):
        # Base metrics that influence other values
        self.user_id = user_id
        self.age = 30
        self.fitness_level = 7  # Scale 1-10
        self.stress_level = 3   # Scale 1-10
        self.last_update = time.time()
        
        # Initialize with reasonable starting values
        self.heart_rate = 65
        self.spo2 = 98
        self.respiratory_rate = 14
        self.body_temperature = 36.6
        self.blood_pressure = {"systolic": 120, "diastolic": 80}
        self.steps = 0
        self.calories_burned = 0
        self.body_battery = 100
        self.stress_score = 25
        self.sleep_score = 85
        
        # Daily targets
        self.daily_step_goal = 10000
        self.daily_calorie_goal = 2500
        
        # Time-based patterns
        self.day_started = datetime.now().replace(hour=0, minute=0, second=0)
        
    def _get_time_factor(self) -> float:
        """Returns a factor (0-1) based on time of day to simulate daily patterns."""
        current_time = datetime.now()
        hour = current_time.hour + current_time.minute / 60
        
        # Simulate daily rhythm (peaks at 3PM, lowest at 3AM)
        time_factor = math.sin((hour - 3) * math.pi / 12)
        return (time_factor + 1) / 2

    def _add_noise(self, value: float, noise_level: float = 0.02) -> float:
        """Add random noise to a value."""
        noise = random.uniform(-noise_level, noise_level) * value
        return value + noise

    def update(self):
        """Update all health metrics based on time of day and random factors."""
        current_time = time.time()
        elapsed_minutes = (current_time - self.last_update) / 60
        time_factor = self._get_time_factor()
        
        # Update heart rate (60-100 bpm, influenced by activity and time of day)
        base_hr = 60 + (40 * time_factor)
        self.heart_rate = self._add_noise(base_hr, 0.05)
        
        # Update SpO2 (95-100%)
        self.spo2 = min(100, self._add_noise(97 + (2 * time_factor), 0.01))
        
        # Update respiratory rate (12-20 breaths per minute)
        self.respiratory_rate = self._add_noise(14 + (4 * time_factor))
        
        # Update body temperature (36.1-37.2°C)
        self.body_temperature = self._add_noise(36.3 + (0.8 * time_factor), 0.01)
        
        # Update blood pressure
        bp_factor = time_factor * 0.15  # 15% variation through the day
        self.blood_pressure["systolic"] = self._add_noise(120 + (20 * bp_factor))
        self.blood_pressure["diastolic"] = self._add_noise(80 + (10 * bp_factor))
        
        # Update steps (based on time and activity)
        if 6 <= datetime.now().hour <= 22:  # Only add steps during waking hours
            new_steps = int(elapsed_minutes * random.uniform(10, 100) * time_factor)
            self.steps += new_steps
            
        # Update calories
        base_calories_per_minute = 1.2  # Base metabolic rate
        activity_calories = elapsed_minutes * random.uniform(0.5, 4) * time_factor
        self.calories_burned += base_calories_per_minute * elapsed_minutes + activity_calories
        
        # Update body battery (0-100)
        if 23 <= datetime.now().hour or datetime.now().hour <= 6:
            # Recharge during typical sleep hours
            self.body_battery = min(100, self.body_battery + (elapsed_minutes * 0.2))
        else:
            # Drain during day
            drain_rate = 0.1 * (1 + time_factor)
            self.body_battery = max(5, self.body_battery - (elapsed_minutes * drain_rate))
            
        # Update stress score (0-100)
        time_stress = abs(math.sin(time.time() / 3600)) * 30  # Varies throughout the day
        random_stress = random.uniform(-10, 10)
        self.stress_score = max(0, min(100, time_stress + random_stress))
        
        self.last_update = current_time

    def get_metrics(self) -> Dict:
        """Return current health metrics."""
        self.update()
        return {
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id,
            "heart_rate": round(self.heart_rate, 1),
            "spo2": round(self.spo2, 1),
            "respiratory_rate": round(self.respiratory_rate, 1),
            "body_temperature": round(self.body_temperature, 1),
            "blood_pressure": {
                "systolic": round(self.blood_pressure["systolic"]),
                "diastolic": round(self.blood_pressure["diastolic"])
            },
            "steps": self.steps,
            "calories_burned": round(self.calories_burned),
            "body_battery": round(self.body_battery),
            "stress_score": round(self.stress_score),
            "sleep_score": self.sleep_score,
            "daily_progress": {
                "steps": {
                    "current": self.steps,
                    "goal": self.daily_step_goal,
                    "percentage": round((self.steps / self.daily_step_goal) * 100, 1)
                },
                "calories": {
                    "current": round(self.calories_burned),
                    "goal": self.daily_calorie_goal,
                    "percentage": round((self.calories_burned / self.daily_calorie_goal) * 100, 1)
                }
            }
        }

# FastAPI application
app = FastAPI(title="Health Metrics Simulator")

# Store user metrics
user_metrics: Dict[str, HealthMetrics] = {}

@app.get("/health/{user_id}")
async def get_health_metrics(user_id: str):
    """Get current health metrics for a user."""
    if user_id not in user_metrics:
        user_metrics[user_id] = HealthMetrics(user_id)
    return user_metrics[user_id].get_metrics()

@app.get("/health/{user_id}/history")
async def get_health_history(user_id: str, hours: int = 24):
    """Get historical health metrics for a user."""
    if user_id not in user_metrics:
        user_metrics[user_id] = HealthMetrics(user_id)
        
    history = []
    current_time = datetime.now()
    
    # Generate historical data points
    for hour in range(hours, 0, -1):
        timestamp = current_time - timedelta(hours=hour)
        metrics = user_metrics[user_id].get_metrics()
        metrics["timestamp"] = timestamp.isoformat()
        history.append(metrics)
        
    return history