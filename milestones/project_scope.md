# Week 2 — Short project details

## Project title
Smart Agriculture Using IoT and AI for Moisture Prediction

## Problem
Farmers may irrigate by fixed schedules or manual inspection. This can waste water and labor when soil and weather conditions vary.

## Proposed solution
Use soil-moisture, temperature, humidity, light, and water-level readings from an ESP32/Arduino. Send readings over Wi-Fi to a backend and show them on a web dashboard. A prediction component estimates the near-term soil-moisture trend and supports an irrigation recommendation. A relay and pump are proposed hardware outputs.

## Objectives
- Monitor field and environmental conditions.
- Store sensor readings and display recent conditions.
- Predict near-term soil moisture from historical readings.
- Demonstrate threshold-based irrigation logic with a software relay state.
- Reduce avoidable irrigation through data-informed monitoring.

## Users and scope
Primary user: farmer or project evaluator. The prototype demonstrates one field zone. Crop-specific moisture ranges, weather forecasts, multiple zones, and real hardware control are future work.

## Components
ESP32/Arduino, capacitive soil moisture sensor, temperature/humidity sensor, light sensor, water-level sensor, isolated relay module, pump, Wi-Fi, API/database, and web dashboard.

## Expected outcome
A local end-to-end software prototype that accepts sample sensor readings, stores them, presents dashboard values, produces an explainable moisture-trend forecast, and demonstrates an irrigation recommendation. No real hardware is connected in this software prototype.
