from rich.console import Console # For better console output formatting
from collections import deque # For using a queue to store recent readings
import paho.mqtt.client as mqttClient 
import sqlite3, json, datetime, time
import sys

# constants 
console = Console()
QUEUE = deque(maxlen=5)

'''
    emoji reference:
    ➜ ⚠︎ ⦸ ✖ ✔ ↻ ⓘ  
'''

# write data to sqlite database
def write_to_db():
    if len(QUEUE) == 5:
        try:
            conn = sqlite3.connect("../../db/Sensor_Reading_Records.db")
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hivemq_sensor_readings (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    photoresistor REAL NOT NULL,
                    microphone REAL NOT NULL
                )
            ''')
            
            # Insert data from the queue into the database
            if len(QUEUE) == 5:
                cursor.execute('''
                    INSERT INTO hivemq_sensor_readings (timestamp, temperature, humidity, photoresistor, microphone)
                    VALUES (?, ?, ?, ?, ?)
                ''', (QUEUE[0], QUEUE[1], QUEUE[2], QUEUE[3], QUEUE[4]))
                conn.commit()
                console.print(f"[green]✔[/green] Data written to database.")
        
        except Exception as e:
            console.print(f"[red]❌[/red] Database Error: {e}")
        
        finally:
            QUEUE.clear() # Clear the queue after writing to the database
            conn.close()

# Callback functions
def temperature_humidity_callback(client, userdata, payload) -> None:
    # Parse the JSON payload
    data = json.loads(payload.payload.decode("utf-8"))
    
    # Reading timestamp
    timestamp = int(time.time())
    
    # Extract temperature and humidity values
    temperature = data.get("temperature")
    humidity = data.get("humidity")
    
    # Store the readings in the queue
    QUEUE.append(timestamp)
    QUEUE.append(temperature)
    QUEUE.append(humidity)
    
    # For Debugging: Print the values to the console
    console.print(f"[green]➜[/green] Temperature: [blue]{temperature}[/blue], Humidity: [blue]{humidity}[/blue]")

def photoresistor_callback(client, userdata, payload) -> None:
    data = json.loads(payload.payload.decode("utf-8"))
    photoresistor = data.get("brightness")
    QUEUE.append(photoresistor)
    # For Debugging: Print the value to the console
    console.print(f"[green]➜[/green] Photoresistor: [blue]{photoresistor}[/blue]") 
    
def microphone_callback(client, userdata, payload) -> None:
    data = json.loads(payload.payload.decode("utf-8"))
    microphone = data.get("noise")
    QUEUE.append(microphone)
    write_to_db()
    # For Debugging: Print the value to the console
    console.print(f"[green]➜[/green] Microphone: [blue]{microphone}[/blue]")
    
# class
class RoomMonitorClient:
    def __init__(self) -> None:
        self.BROKER:str = "broker.hivemq.com"
        self.PORT:int = 1883
        self.__TOPICS:list = [
            # topic names and qos levels
            ("sensor/ky-015/temperature-humidity/data", 1),
            ("sensor/ky-018/photoresistor/data", 1),
            ("sensor/ky-037/microphone/data", 1),
        ]
    
    def on_connect(self, client, userdata, flags, status_code) -> None:
        
        # Check if connection was successful
        if status_code == 0:
            console.print(f"[green]➜[/green] Connected to [blue]broker.hivemq.com[/blue]")
            
            # subscribe to topics
            client.subscribe(self.__TOPICS)
            
            # add callbacks for each topic
            client.message_callback_add("sensor/ky-015/temperature-humidity/data", temperature_humidity_callback)
            client.message_callback_add("sensor/ky-018/photoresistor/data", photoresistor_callback)
            client.message_callback_add("sensor/ky-037/microphone/data", microphone_callback)
            
        else:
            console.print(f"[yellow]⚠️[/yellow] Connection Failed with code: {status_code}")
    
    def on_message(self, client, userdata, msg) -> None:
        console.print(f"[green]➜[/green] [{msg.topic}]: {msg.payload.decode('utf-8')}")

    def on_disconnect(self, client, userdata, status_code) -> None:
        if status_code != 0:
            console.print(f"[yellow]↻[/yellow] Disconnected with code: {status_code}")
    
    # Connect to MQTT Broker and return the client instance
    def mqtt_client(self) -> mqttClient.Client:
        subscriber = mqttClient.Client(client_id="room-monitor-hshl-001")
        subscriber.on_connect = self.on_connect
        subscriber.on_message = self.on_message
        subscriber.on_disconnect = self.on_disconnect
        subscriber.connect(self.BROKER, self.PORT, keepalive=60)
        return subscriber
    
# Main Entry Point
if __name__ == "__main__":
    try:
        room_monitor_handler  = RoomMonitorClient()
        mqtt = room_monitor_handler.mqtt_client()
        
        # Start the MQTT client loop to listen for messages
        mqtt.loop_forever()
        
    except KeyboardInterrupt:
        print()
        console.print(f"[green]➜[/green] Exiting...")
        mqtt.disconnect()
        sys.exit(0)
        
    except Exception as e:
        console.print(f"[red]❌[/red] Error: {e}")