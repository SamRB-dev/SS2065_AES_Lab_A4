Sure — here’s the markdown directly so you can copy it:

````markdown
<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Share+Tech+Mono&weight=700&size=40&pause=1000&color=00FF88&background=00000000&center=true&width=650&lines=Smart+Room+Monitoring+System" alt="Typing SVG" />
</div>

# Smart Room Monitoring System

The system monitors the comfort level of a room by measuring temperature, humidity, light level, noise level, and possible occupancy/distance. The collected data is sent through MQTT to a Python client, stored in SQLite, and presented through a dashboard where users can view the current room status.

The project now contains two embedded-system implementations:

1. the **original physical hardware implementation**, and
2. a newer **single-ESP32-S3 simulation implementation** used to validate the architecture before moving to PCB design.

---

# Physical Hardware Implementation

The original physical implementation uses the following hardware.

### Hardware

- ESP32 x1
- Raspberry Pi 3 Model B v2 x1
- Arduino WiFi Rev2 x2

### Sensors

- KY-015 Combi Sensor (Temperature & Humidity) x1
- KY-018 Photoresistor x2
- KY-037 or KY-038 Microphone Sound Sensor x1

### Protocol

- MQTT

The physical implementation uses separate embedded boards for the different sensor publishers.

The corresponding publisher programs are located in:

```text
Project/src/sensor-publishers/
````

including:

```text
Temperature-Humidity-Sensor.ino
photoregister.ino
Microphone.ino
```

The MQTT data is received by the Python client and stored in the SQLite database for use by the dashboard.

---

# ESP32-S3 Simulation Implementation

As a next development stage, the sensor-node architecture was redesigned around a **single ESP32-S3**.

The simulation consolidates the sensor-reading and MQTT-publishing responsibilities onto one ESP32-S3 while keeping the existing MQTT topics and backend software compatible with the original project.

## Cirkit Designer Simulation

[Open the ESP32-S3 Smart Room Monitoring Simulation](https://app.cirkitdesigner.com/project/668acf81-1f05-40f3-9d74-6e21bc692d80)

The simulation uses:

* ESP32-S3 x1
* DHT11 / temperature-humidity sensor
* Photoresistor module
* Microphone sound sensor

The ESP32-S3 simulation communicates with the existing Python client running on the local machine through the MQTT broker.

---

## ESP32-S3 Pin Configuration

| Sensor         | Signal | ESP32-S3 Pin |
| -------------- | ------ | -----------: |
| Photoresistor  | AO     |        GPIO4 |
| Microphone     | AO     |        GPIO6 |
| DHT11 / KY-015 | DATA   |        GPIO7 |

```text
Photoresistor AO ─────► GPIO4
Microphone AO ────────► GPIO6
DHT11 DATA ───────────► GPIO7
```

---

# FreeRTOS Architecture

The ESP32-S3 simulation uses FreeRTOS to separate sensor acquisition from MQTT communication.

```text
                     ESP32-S3
              ┌────────────────────┐
              │                    │
DHT11 ───────►│ DHT Task           │
              │        │           │
Light ───────►│ Light Task ─────┐  │
              │                 │  │
Microphone ──►│ Mic Task ───────┼──┼──► FreeRTOS Queue
              │                 │  │           │
              └────────────────────┘           ▼
                                          MQTT Task
                                              │
                                              ▼
                                         MQTT Broker
```

The main tasks are:

* **DHT Task** — reads temperature and humidity
* **Light Task** — reads the photoresistor
* **Microphone Task** — reads the microphone signal
* **MQTT Task** — handles Wi-Fi and MQTT publishing
* **FreeRTOS Queue** — transfers sensor data between tasks

This architecture provides a clean transition from simulation to the planned ESP32-S3 PCB implementation.

---

# MQTT Communication

### Broker

```text
broker.hivemq.com
```

### Port

```text
1883
```

The original implementation and the ESP32-S3 simulation use the same MQTT topics.

## Temperature & Humidity

```text
sensor/ky-015/temperature-humidity/data
```

Example payload:

```json
{
  "temperature": 25.0,
  "humidity": 60.0
}
```

## Photoresistor

```text
sensor/ky-018/photoresistor/data
```

Example payload:

```json
{
  "brightness": 68
}
```

## Microphone

```text
sensor/ky-037/microphone/data
```

Example payload:

```json
{
  "noise": 42
}
```

---

# End-to-End Simulation

The ESP32-S3 simulation has been validated with the existing backend.

```text
Simulated Sensors
       │
       ▼
    ESP32-S3
       │
       ▼
 FreeRTOS Tasks
       │
       ▼
      MQTT
       │
       ▼
broker.hivemq.com
       │
       ▼
RoomMonitorClient.py
       │
       ▼
     SQLite
       │
       ▼
 Flask Dashboard
```

Sensor values changed in the simulation are successfully:

1. read by the ESP32-S3,
2. processed by the FreeRTOS tasks,
3. published through MQTT,
4. received by the Python MQTT client,
5. stored in the SQLite database, and
6. made available to the existing dashboard.

This validates the single-ESP32-S3 software architecture before moving to PCB design.

---

# Project Progress Checklist

## Original Project

* [x] Requirement Analysis (diagrams)
* [x] Connect to Data Storage: SQLite
* [x] MQTT Subscriber: Python
* [x] MQTT Publisher: C++
* [x] Data Presentation: Dashboard

### MQTT Topics

* [x] `sensor/ky-015/temperature-humidity/data`
* [x] `sensor/ky-018/photoresistor/data`
* [x] `sensor/ky-037/microphone/data`

## ESP32-S3 Revision

* [x] Single ESP32-S3 sensor-node simulation
* [x] FreeRTOS task implementation
* [x] Temperature and humidity acquisition
* [x] Photoresistor acquisition
* [x] Microphone acquisition
* [x] MQTT publishing
* [x] Integration with existing Python MQTT client
* [x] Integration with existing SQLite database
* [x] Integration with existing dashboard
* [x] End-to-end simulation validation

## PCB Development

* [ ] KiCad schematic
* [ ] Footprint assignment
* [ ] Component placement
* [ ] PCB routing
* [ ] Ground plane
* [ ] Electrical Rule Check
* [ ] Design Rule Check
* [ ] 3D board verification
* [ ] Gerber generation
* [ ] PCB manufacturing
* [ ] Physical ESP32-S3 hardware validation

---

# PCB Development

The next stage is to design a custom PCB around the validated single-ESP32-S3 architecture.

The PCB will reproduce the main sensor connections validated in the simulation:

```text
GPIO4 → Photoresistor AO
GPIO6 → Microphone AO
GPIO7 → DHT11 DATA
```

The planned board will provide:

* ESP32-S3 DevKit integration
* temperature/humidity sensor connection
* photoresistor connection
* microphone connection
* shared power distribution
* common ground
* clean analog routing
* sensor headers/connectors
* a layout suitable for manufacturing

---

# Run the Project

### Create Virtual Environment

```shell
python3 -m venv .venv
```

### Activate `.venv`

Linux/macOS:

```shell
source .venv/bin/activate
```

Windows:

```shell
.venv\Scripts\activate
```

### Install Dependencies

```shell
pip install -r requirements.txt
```

### Run the Client

From the `Project` directory:

```shell
cd src/client
python3 RoomMonitorClient.py
```

### Run the Dashboard

From the `Project` directory:

```shell
cd src/dashboard
python3 Flask-Server.py
```

---

# Resources

[HiveMQ](https://www.hivemq.com/blog/implementing-mqtt-in-python/)

[Py paho-mqtt](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python)

[Paho-mqtt Documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html#paho.mqtt.client.Client.connect)

[HiveMQ Security](https://www.hivemq.com/blog/mqtt-security-fundamentals-securing-mqtt-systems/) <- *IMPORTANT*

---

# Current Development Stage

The **original physical implementation** remains part of the project and is documented separately from the newer **single-ESP32-S3 FreeRTOS simulation**.

The simulation is working end-to-end with the existing MQTT client, SQLite database, and dashboard.

The next development stage is the **ESP32-S3 PCB design**.

```
```
