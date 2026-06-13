<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Share+Tech+Mono&weight=700&size=40&pause=1000&color=00FF88&background=00000000&center=true&width=650&lines=Smart+Room+Monitoring+System" alt="Typing SVG" />
</div>

The system monitors the comfort level of a room by measuring temperature, humidity, light level, noise level, and possible occupancy/distance. The collected data will be sent to a web or mobile dashboard where users can see the current room status.

### Hardwares
- ESP32 per sensor x1
- Raspberry Pi 3 Model B v2 x1

#### Sensors:
- KY-015 Combi Sensor (Temperature & Humidity) x1
- KY-018 Photoresistor x2
- KY-037 or KY-038 Microphone Sound Sensor x1

#### Protocols: MQTT


### Project Progress Checklist

- [ ] Requirement Analysis (diagrams)
- [ ] Connect to Data Storage: SQLite
- [x] MQTT Subscriber: Python
- [ ] MQTT Publisher: C++
    #### publisher topic suggestion: 
    - [x] sensor/ky-015/temperature/data
    - [x] sensor/ky-015/humidity/data
    - [x] sensor/ky-018/photoresistor/data
    - [x] sensor/ky-037/microphone/data
- [ ] Data Presentation: Web App or Mobile App

### Resources 

[HiveMQ](https://www.hivemq.com/blog/implementing-mqtt-in-python/)

[Py paho-mqtt](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python)

[Paho-mqtt Documentation](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html#paho.mqtt.client.Client.connect)


[HiveMQ Security](https://www.hivemq.com/blog/mqtt-security-fundamentals-securing-mqtt-systems/) <- *IMPORTANT*

# Run the Project
### Create Virtual Environment
```shell
python3 -m venv .venv
```

### Activate .venv
```shell
source .venv/bin/activate
```

### Install Dependencies
```shell
pip install -r requirements.txt
```

### Run 
```shell
cd Projects/src/client/
python3 RoomMonitorClient.py
```