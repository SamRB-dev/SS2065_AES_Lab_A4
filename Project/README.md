<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Share+Tech+Mono&weight=700&size=40&pause=1000&color=00FF88&background=00000000&center=true&width=650&lines=Smart+Room+Monitoring+System" alt="Typing SVG" />
</div>

# Smart Room Monitoring System

The **Smart Room Monitoring System (SRMS)** is an IoT-based environmental monitoring platform for measuring room conditions such as temperature, humidity, ambient light, and noise.

Sensor nodes publish measurements over **MQTT** to a central broker. A Python subscriber receives the data, stores it in an **SQLite database**, and exposes the latest measurements through a **Flask-based dashboard**.

The project includes:

- an original multi-controller physical implementation,
- a single-ESP32-S3 FreeRTOS simulation,
- an existing MQTT + database + dashboard backend,
- and a planned custom ESP32-S3 PCB implementation.

---

### System Architecture

```text
                    MQTT
Sensor Nodes ─────────────────► HiveMQ Broker
                                    │
                                    ▼
                           RoomMonitorClient.py
                                    │
                                    ▼
                              SQLite Database
                                    │
                                    ▼
                              Flask Dashboard
```

The MQTT interface is shared between the original hardware implementation and the newer ESP32-S3 architecture, allowing the backend to remain unchanged.

---

### Physical Implementation

The original prototype uses multiple microcontrollers as independent sensor publishers.

#### Hardware

| Component | Quantity | Purpose |
|---|---:|---|
| ESP32 | 1 | Sensor acquisition / MQTT publisher |
| Arduino WiFi Rev2 | 2 | Sensor acquisition / MQTT publishers |
| Raspberry Pi 3 Model B v2 | 1 | Backend / client host |
| KY-015 | 1 | Temperature and humidity |
| KY-018 | 2 | Ambient light sensing |
| KY-037 / KY-038 | 1 | Sound / noise sensing |

#### Communication

| Interface | Usage |
|---|---|
| Wi-Fi | Sensor node connectivity |
| MQTT | Sensor data transport |
| SQLite | Persistent sensor storage |
| HTTP / Flask | Dashboard interface |

The original publisher firmware is located in:

```text
Project/src/sensor-publishers/
```

---

### ESP32-S3 Revision

The embedded architecture was later redesigned around a **single ESP32-S3**.

Instead of using separate microcontrollers for each sensor publisher, one ESP32-S3 performs sensor acquisition and MQTT communication.

#### Simulation Hardware

| Device | Signal | ESP32-S3 Pin |
|---|---|---:|
| Photoresistor | Analog Output | GPIO4 |
| Microphone | Analog Output | GPIO6 |
| DHT11 | Data | GPIO7 |

#### Cirkit Designer

The ESP32-S3 implementation is simulated in Cirkit Designer:

[ESP32-S3 SRMS Simulation](https://app.cirkitdesigner.com/project/668acf81-1f05-40f3-9d74-6e21bc692d80)

---

### FreeRTOS Architecture

The ESP32-S3 implementation uses FreeRTOS to separate sensor acquisition from communication.

```text
             ┌───────────────┐
DHT11 ──────►│ DHT Task      │
             └───────┬───────┘
                     │
             ┌───────▼───────┐
Light ──────►│ Light Task     │
             └───────┬───────┘
                     │
             ┌───────▼───────┐
Microphone ─►│ Mic Task       │
             └───────┬───────┘
                     │
                     ▼
              FreeRTOS Queue
                     │
                     ▼
                MQTT Task
                     │
                     ▼
                HiveMQ Broker
```

#### Tasks

| Task | Responsibility |
|---|---|
| `DHT Task` | Read temperature and humidity |
| `Light Task` | Read and process photoresistor ADC values |
| `Microphone Task` | Read and process microphone ADC values |
| `MQTT Task` | Maintain network connection and publish sensor data |

Using a queue separates sensor acquisition from network communication and provides a cleaner architecture for the physical ESP32-S3 implementation.

---

### MQTT Interface

#### Broker

| Parameter | Value |
|---|---|
| Broker | `broker.hivemq.com` |
| Port | `1883` |
| Protocol | MQTT |

#### Topics

| Sensor | MQTT Topic | Payload |
|---|---|---|
| Temperature / Humidity | `sensor/ky-015/temperature-humidity/data` | `{"temperature":25.0,"humidity":60.0}` |
| Light | `sensor/ky-018/photoresistor/data` | `{"brightness":68}` |
| Microphone | `sensor/ky-037/microphone/data` | `{"noise":42}` |

The same topics are used by both the original implementation and the ESP32-S3 revision.

---

### Backend

#### MQTT Subscriber

```text
Project/src/client/RoomMonitorClient.py
```

The Python MQTT client:

1. connects to the HiveMQ broker,
2. subscribes to all sensor topics,
3. parses incoming JSON payloads,
4. timestamps each measurement,
5. stores the readings in SQLite.

#### Database

```text
Project/db/Sensor_Reading_Records.db
```

| Table | Stored Data |
|---|---|
| `temperature_humidity_readings` | temperature, humidity |
| `photoresistor_readings` | light intensity |
| `microphone_readings` | sound level |

#### Dashboard

```text
Project/src/dashboard/Flask-Server.py
```

The Flask dashboard reads the latest measurements from SQLite and displays the current room-monitoring status.

---

#### End-to-End Validation

The ESP32-S3 simulation has been validated with the existing backend.

```text
Cirkit Sensors
      │
      ▼
ESP32-S3
      │
      ▼
FreeRTOS Tasks
      │
      ▼
MQTT Publisher
      │
      ▼
HiveMQ
      │
      ▼
Python Subscriber
      │
      ▼
SQLite
      │
      ▼
Flask Dashboard
```

Changing sensor values in the simulation results in corresponding updates being received by the Python client and stored in the database.

This validates the software architecture before transferring the design to physical hardware.

---

### Project Demo

A recorded demonstration of the complete system is available in:

```text
Project/demo/
```

[View Project Demo](Project/demo/Project_Demo.mp4)

---

### Repository Structure

```text
Project/
│
├── db/
│   └── Sensor_Reading_Records.db
│
├── demo/
│   └── Project_Demo.mp4
│
├── src/
│   ├── client/
│   │   └── RoomMonitorClient.py
│   │
│   ├── dashboard/
│   │   └── Flask-Server.py
│   │
│   └── sensor-publishers/
│       ├── Temperature-Humidity-Sensor.ino
│       ├── photoregister.ino
│       └── Microphone.ino
│
├── Technical Documentation/
├── datasheets/
├── analysis/
└── README.md
```

---

### Running the Project

#### Create a Virtual Environment

```shell
python3 -m venv .venv
```

#### Activate the Environment

Linux / macOS:

```shell
source .venv/bin/activate
```

Windows:

```shell
.venv\Scripts\activate
```

#### Install Dependencies

```shell
pip install -r requirements.txt
```

#### Start the MQTT Subscriber

```shell
cd Project/src/client
python3 RoomMonitorClient.py
```

#### Start the Dashboard

Open another terminal:

```shell
cd Project/src/dashboard
python3 Flask-Server.py
```

---

### Development Status

| Stage | Status |
|---|---|
| Original physical prototype | ✅ Complete |
| MQTT publishers | ✅ Complete |
| Python MQTT subscriber | ✅ Complete |
| SQLite storage | ✅ Complete |
| Flask dashboard | ✅ Complete |
| ESP32-S3 simulation | ✅ Complete |
| FreeRTOS architecture | ✅ Complete |
| End-to-end MQTT simulation | ✅ Complete |
| KiCad schematic | 🚧 Next |
| PCB layout | ⏳ Planned |
| PCB manufacturing | ⏳ Planned |
| Physical ESP32-S3 validation | ⏳ Planned |

---

### PCB Revision

The next revision will consolidate the sensor node onto an **ESP32-S3 carrier PCB**.

The validated signal mapping is:

| Signal | ESP32-S3 |
|---|---:|
| Photoresistor AO | GPIO4 |
| Microphone AO | GPIO6 |
| DHT11 DATA | GPIO7 |

The PCB design will focus on:

- ESP32-S3 DevKit integration
- sensor connectors
- shared 3.3 V power distribution
- common ground plane
- clean analog routing
- compact component placement
- manufacturable KiCad layout

---

### Resources

- [HiveMQ](https://www.hivemq.com/blog/implementing-mqtt-in-python/)
- [Paho MQTT Python](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python)
- [Paho MQTT Documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html#paho.mqtt.client.Client.connect)
- [HiveMQ Security Fundamentals](https://www.hivemq.com/blog/mqtt-security-fundamentals-securing-mqtt-systems/)
