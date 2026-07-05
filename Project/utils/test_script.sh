#!/bin/bash

HOST="broker.hivemq.com"
PORT=1883
INTERVAL=5    # seconds between each full cycle

while true; do
    mosquitto_pub -h $HOST -p $PORT -t "sensor/ky-015/temperature-humidity/data" -m '{"temperature": 23.5, "humidity": 60.2}' -q 1
    mosquitto_pub -h $HOST -p $PORT -t "sensor/ky-018/photoresistor/data"        -m '{"brightness": 400}' -q 1
    mosquitto_pub -h $HOST -p $PORT -t "sensor/ky-037/microphone/data"          -m '{"noise": 45.1}' -q 1

    echo "Cycle published. Waiting ${INTERVAL}s..."
    sleep $INTERVAL
done