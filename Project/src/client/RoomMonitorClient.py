from http import client

from rich.console import Console
import paho.mqtt.client as mqttClient 
import sqlite3, logging
import sys

# constants 
console = Console()
'''
    emoji reference:
    ➜ : U+279C (Heavy Round-Tipped Rightwards Arrow)
    ⚠︎ : U+26A0 (Warning Sign)
    ⃠ : U+20E0 (Combining Enclosing Circle Backslash)
    ⦸ : U+29B8 (Circled X)
    ✖ : U+2716 (Heavy Multiplication X)
    
'''
# Callback functions
def temparature_callback(client, userdata, payload) -> None:
    temparature = payload.payload.decode("utf-8")
    console.print(f"[green]➜[/green] Temparature: [blue]{temparature}[/blue]")

def humidity_callback(client, userdata, payload) -> None:
    humidity = payload.payload.decode("utf-8")
    console.print(f"[green]➜[/green] Humidity: [blue]{humidity}[/blue]")

def photoresistor_callback(client, userdata, payload) -> None:
    photoresistor = payload.payload.decode("utf-8")
    console.print(f"[green]➜[/green] Photoresistor: [blue]{photoresistor}[/blue]") 
    
def microphone_callback(client, userdata, payload) -> None:
    microphone = payload.payload.decode("utf-8")
    console.print(f"[green]➜[/green] Microphone: [blue]{microphone}[/blue]")
    
     
# class
class RoomMonitorClient:
    def __init__(self) -> None:
        self.BROKER:str = "broker.hivemq.com"
        self.PORT:int = 1883
        self.__TOPICS:list = [
            ("sensor/ky-015/temperature/data", 1),
            ("sensor/ky-015/humidity/data", 1),
            ("sensor/ky-018/photoresistor/data", 1),
            ("sensor/ky-037/microphone/data", 1),
        ]
    
    def on_connect(self, client, userdata, flags, status_code) -> None:
        
        if status_code == 0:
            console.print(f"[green]➜[/green] Connected to [blue]broker.hivemq.com[/blue]")
            
            # subscribe to topics
            client.subscribe(self.__TOPICS)
            
            # add callbacks for each topic
            client.message_callback_add("sensor/ky-015/temperature/data", temparature_callback)
            client.message_callback_add("sensor/ky-015/humidity/data", humidity_callback)
            client.message_callback_add("sensor/ky-018/photoresistor/data", photoresistor_callback)
            client.message_callback_add("sensor/ky-037/microphone/data", microphone_callback)
            
        else:
            console.print(f"[red]✖[/red]  Connection Failed with code: {status_code}")
    
    def on_message(self, client, userdata, msg) -> None:
        console.print(f"[green]➜[/green] [{msg.topic}]: {msg.payload.decode('utf-8')}")

    def on_disconnect(self, client, userdata, status_code) -> None:
        if status_code != 0:
            console.print(f"[red]✖[/red] Disconnected with code: {status_code}")
    
    def mqtt_client(self) -> mqttClient.Client:
        subscriber = mqttClient.Client(client_id="room-monitor-hshl-001")
        subscriber.on_connect = self.on_connect
        subscriber.on_message = self.on_message
        subscriber.on_disconnect = self.on_disconnect
        subscriber.connect(self.BROKER, self.PORT, keepalive=60)
        return subscriber
if __name__ == "__main__":
    try:
        room_monitor_handler = RoomMonitorClient()
        subscriber = room_monitor_handler.mqtt_client()
        subscriber.loop_forever()
    except KeyboardInterrupt:
        console.print(f"[green]➜[/green] Exiting...")
        subscriber.disconnect()
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]✖[/red] Error: {e}")
    