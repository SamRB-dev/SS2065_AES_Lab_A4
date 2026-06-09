#include <ArduinoMqttClient.h>
#include <WiFiNINA.h>


#define RESISTOR_PIN A5

char ssid[] = "Sadim Rahman's S25 Ultra";
char pass[] = "1234567890";


WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "broker.hivemq.com";
int port = 1883;

const char topic[] = "sensor/ky-018/photoresistor/data";

const long interval = 5000;
unsigned long previousMillis = 0;

// Sensor Specific variable
int rawValue;
float resistance;
float voltage;

void setup() {
  Serial.begin(9600);

  while (!Serial) {
    ;
  }

  Serial.print("Attempting to connect to SSID: ");
  Serial.println(ssid);

  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    Serial.print(".");
    delay(5000);
  }

  Serial.println();
  Serial.println("You're connected to the network");
  Serial.println();

  Serial.print("Attempting to connect to the MQTT broker: ");
  Serial.println(broker);

  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT connection failed! Error code = ");
    Serial.println(mqttClient.connectError());

    while (1);
  }

  Serial.println("You're connected to the MQTT broker!");
  Serial.println();
}

void loop() {
  mqttClient.poll();

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;


    // Sensor specific code
    rawValue = analogRead(RESISTOR_PIN);
    voltage = rawValue * (5.0/1023) * 1000;     
    resistance = 10000 * (voltage / (5000.0 - voltage));

    
    mqttClient.beginMessage(topic);

    mqttClient.print("{\"Resistance\":");
    mqttClient.print(resistance);
    mqttClient.print("}");

    mqttClient.endMessage();

    Serial.print("Data sent to topic: ");
    Serial.println(topic);
    Serial.println();
  }
}