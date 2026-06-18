from rich.console import Console # For better console output formatting
import paho.mqtt.client as mqttClient
import sqlite3, json, time
import sys

# constants
console = Console()
DB_PATH = "../../db/Sensor_Reading_Records.db"

'''
    emoji reference:
    ➜ ⚠︎ ⦸ ✖ ✔ ↻ ⓘ
'''

# one-time database setup, called once at startup
def init_db() -> None:
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_humidity_readings (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photoresistor_readings (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                light_intensity REAL NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS microphone_readings (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                sound_level REAL NOT NULL
            )
        ''')

        connection.commit()
        console.print("[green]✔[/green] Database ready with all three tables.")

    except Exception as e:
        console.print(f"[red]❌[/red] Database init error: {e}")

    finally:
        connection.close()


# write data to sqlite database
def write_to_db(value, timestamp: int, mode: str) -> int:
    try:
        # Create connection to DB
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        match mode:
            case "temperature_humidity":
                # Check if the value is a list
                if isinstance(value, list) and len(value) == 2:
                    cursor.execute('''
                        INSERT INTO temperature_humidity_readings (timestamp, temperature, humidity)
                        VALUES (?, ?, ?)
                    ''', (timestamp, value[0], value[1]))
                else:
                    console.print("[yellow]⚠︎[/yellow] Invalid temperature/humidity payload, skipped.")
                    return 1

            case "photoresistor":
                cursor.execute('''
                    INSERT INTO photoresistor_readings (timestamp, light_intensity)
                    VALUES (?, ?)
                ''', (timestamp, value))

            case "microphone":
                cursor.execute('''
                    INSERT INTO microphone_readings (timestamp, sound_level)
                    VALUES (?, ?)
                ''', (timestamp, value))

            case _:
                console.print(f"[yellow]⚠︎[/yellow] Unknown mode '{mode}', nothing written.")
                return 1

        connection.commit()
        console.print(f"[green]✔[/green] {mode} data written to database.")
        return 0

    except Exception as e:
        console.print(f"[red]❌[/red] Database Error: {e}")
        return 1

    finally:
        connection.close()


# Callback functions
def temperature_humidity_callback(client, userdata, payload) -> None:
    # Parse the JSON payload
    data = json.loads(payload.payload.decode("utf-8"))

    # Reading timestamp
    timestamp = int(time.time())

    # Extract temperature and humidity values
    temperature = data.get("temperature")
    humidity = data.get("humidity")

    # For Debugging: Print the values to the console
    console.print(f"[green]➜[/green] Temperature: [blue]{temperature}[/blue], Humidity: [blue]{humidity}[/blue]")

    write_to_db([temperature, humidity], timestamp, "temperature_humidity")

def photoresistor_callback(client, userdata, payload) -> None:
    data = json.loads(payload.payload.decode("utf-8"))
    photoresistor = data.get("brightness")
    timestamp = int(time.time())
    # For Debugging: Print the value to the console
    console.print(f"[green]➜[/green] Photoresistor: [blue]{photoresistor}[/blue]")

    write_to_db(photoresistor, timestamp, "photoresistor")

def microphone_callback(client, userdata, payload) -> None:
    data = json.loads(payload.payload.decode("utf-8"))
    microphone = data.get("noise")
    timestamp = int(time.time())

    # For Debugging: Print the value to the console
    console.print(f"[green]➜[/green] Microphone: [blue]{microphone}[/blue]")

    write_to_db(microphone, timestamp, "microphone")

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
    init_db()

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