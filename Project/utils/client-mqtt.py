#! /usr/bin/env python3

# Import modules
try:
    import paho.mqtt.client
except ImportError as e:
    print(f"{e}")
    
# Create MQTT client
client = paho.mqtt.client.Client(
    client_id="test-client",
    userdata=None,
    protocol=paho.mqtt.client.MQTTv5,
)

# Enable TLS
client.tls_set(tls_version=paho.mqtt.client.ssl.PROTOCOL_TLS)

# Connect to the broker
client.connect("broker.hivemq.com", 8883)

# Connection
 