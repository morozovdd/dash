# AI Summit Hackathon Project

**Team Name:** DASH
**Team Members:** Daniil Morozov, Caitlin O'Brian, Ke Xu
**Event:** AI Summit Hackathon 2024 at Jarvis center
**Date:** 12 / 11 - 12/ 2024

---

## Table of Contents
- [AI Summit Hackathon Project](#ai-summit-hackathon-project)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
    - [Key Components](#key-components)
    - [Key Agents:](#key-agents)
  - [Repositories:](#repositories)
  - [Technologies Used](#technologies-used)
  - [Installation Instructions](#installation-instructions)
  - [Thank you!!!](#thank-you)


## Project Overview

This project is built for the [AI Summit Hackathon 2024] with the goal of Health service emergency detection pipeline, including heart attack and strokes, from smart watch data. We used a combination of apis, including google map and direction for transforming the location data, Gemini for providing the inference and analysis, Telegram for communicate with the user and emergency contact. We used Fetch.ai's agent structure to let batching data module communicate with analysis module and the emergency module to allow users get the help they needed during crisis.

### Key Components

 - #### Accident Detection Agent:

The core functionality revolves around the AccidentAnalysis model, which flags potential accidents based on health data patterns.
The agent listens for incoming health data messages (via a shared protocol) and processes them for signs of critical health conditions or accidents, based on vital signs, movement, and contextual data.
 - #### Health Data Protocol:

The system uses a shared protocol for communication, where batched health data in a span of a minute is passed to the agent for analysis. The protocol includes information on vital signs (e.g., heart rate, SpO2), movement patterns (e.g., activity state, acceleration), and context (e.g., time of day, location).
The model computes the likelihood of an accident or emergency situation based on the received data, generating an alert response.
 - #### Generative AI Integration (Google Gemini):

The Gemini model is utilized to generate context-aware health data analysis. It processes the data and outputs a decision on whether an accident or emergency alert is necessary.
The model’s output includes a structured response with an alert (true/false) and a reasoning explanation, which is used by the system to trigger further actions.

- #### Alert System:

If an alert is generated (i.e., the analysis detects a high probability of an emergency), the system sends the alert to a decision-maker's address. This decision maker can take appropriate action, such as notifying medical personnel or initiating emergency procedures.
Logging & Error Handling:

The system features extensive logging, where successful analyses are logged for tracking and alerting. Errors encountered during analysis or communication are captured and reported for debugging and system maintenance.

### Key Agents:

 1. ### **Health Monitoring Agent (collector_agent)**:
  Data Models: Defines models for VitalSigns, MovementData, ContextData, and HealthData.
Startup: Initializes storage for data points and timestamp.
Data Fetching: Every 5 seconds, fetches health data via an HTTP request, storing it in memory.
Data Aggregation: Once 5 data points are collected, it aggregates the data into structured format and sends it to another agent (ANALYZER_ADDRESS).

2. ### **Bureau Setup**:
Configures a Bureau to run multiple agents (collector, analyzer, decision maker).
Each agent's address is logged, and environment variables are set for communication.

3. ### **Shared Protocols**:
Health Protocol: Defines a health analysis protocol with structured data for vital signs, blood pressure, movement, and context.
Emergency Protocol: Models for emergency response and notification, including location and medical details.

4. ### **Locator Agent (locator_agent)**:
Geolocation: Utilizes Google Maps API to reverse geocode coordinates and check traffic conditions.
POI Search: Finds Points of Interest (e.g., hospitals) near the user’s location, sends the data to a designated address.
Traffic Conditions: Retrieves real-time traffic data between two locations and sends results.

5. ### **Event Handling**:
Message Handling: The locator agent processes incoming location data (Coordinates), performs POI search, and responds with nearest hospital details and traffic conditions.


## Repositories:

Frontend and backend for the data displaying: https://github.com/morozovdd/health-dashboard

Framework and agent structure for emergency detection:
https://github.com/morozovdd/dash

## Technologies Used

- **Programming Languages:** Python, Javascript (for frontend data dashboard display)
- **Frameworks & Libraries:** Next.js, uagent from Fetch.AI, bureau, unicorn.
- **APIs & Services:** Gemini, Google Map, Telegram, 
- **Database:** Local simulated database
- **Tools & Platforms:** FETCH.AI



## Installation Instructions

To set up and run the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/morozovdd/dash.git

   git clone https://github.com/morozovdd/health-dashboard.git



## Thank you!!! 

Special thanks for Fetch AI for giving us the opportunties of Hackathon at AI SUMMIT NY 2024

