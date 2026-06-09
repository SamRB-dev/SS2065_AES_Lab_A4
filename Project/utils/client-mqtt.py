from paho.mqtt import client 
import os, sys, logging

broker =  "broker.hivemq.com"
port = 1883
topic = "test/topic"

def connect_mqtt() -> client:
    def on_connect(client, userdata, flags, status_code):
        if status_code == 0:
            print("Connected to MQTT")
        else:
            print(f"Connection Failed: {status_code}")
    subscriber = client.Client()
    subscriber.on_connect = on_connect
    subscriber.connect(broker, port)
    return subscriber

def subscribe(client: client):
    def on_message(client, userdata, msg):
        print(msg.payload.decode())
    client.subscribe(topic)
    client.on_message = on_message
    
    
if __name__ == "__main__":
    try:
        client = connect_mqtt()
        subscribe(client)
        client.loop_forever()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(e)
