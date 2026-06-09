import paho.mqtt.client as mqtt_client
import sys

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "sensor/ky-037/microphone/data"

def on_connect(client, userdata, flags, status_code):
    if status_code == 0:
        print("Connected to MQTT Broker")
        client.subscribe(TOPIC, qos=1)
        print(f"Subscribed to: {TOPIC}")
    else:
        print(f"Connection Failed with code: {status_code}")

def on_message(client, userdata, msg):
    print(f"[{msg.topic}] {msg.payload.decode('utf-8')}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnection. Reconnecting...")

def connect_mqtt():
    subscriber = mqtt_client.Client(client_id="room-monitor-sub-001")
    subscriber.on_connect    = on_connect
    subscriber.on_message    = on_message
    subscriber.on_disconnect = on_disconnect
    subscriber.connect(BROKER, PORT, keepalive=60)
    return subscriber

if __name__ == "__main__":
    try:
        client = connect_mqtt()
        client.loop_forever()
    except KeyboardInterrupt:
        print("Disconnecting...")
        client.disconnect()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")