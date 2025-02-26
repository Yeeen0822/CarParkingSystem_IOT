IoT-Based Smart Car Parking System
Project Overview

This project is an IoT-based smart parking system that monitors and manages parking slot availability using Raspberry Pi 4, ESP microcontrollers, and Node-RED for the user interface. The system detects vehicle presence using IR sensors and updates real-time slot availability on a dashboard, optimizing parking efficiency.

Features
✅ Real-time Parking Slot Detection – Uses IR sensors connected to ESP to detect available and occupied slots.
✅ Live Monitoring Dashboard – Displays parking status using Node-RED UI.
✅ Automatic Slot Updates – Raspberry Pi processes data from ESP and updates the parking status dynamically.
✅ Cloud Integration  – Store data in Firebase for remote monitoring.
✅ Indicator LEDs – Green for available slots, Red for occupied slots.

Hardware Components

Raspberry Pi 4 – Main controller for data processing.
ESP (ESP8266/ESP32) – Microcontroller for handling IR sensors.
IR Sensors – Detects vehicle presence.
LEDs – Indicate parking slot availability.
Power Supply – 5V power adapter for Raspberry Pi and ESP.

Software & Technologies Used

Programming Languages: C++
Frameworks & Tools: Node-RED (UI Dashboard), MQTT (for communication), Firebase (for cloud integration)
Communication Protocols: MQTT / HTTP requests between ESP and Raspberry Pi
