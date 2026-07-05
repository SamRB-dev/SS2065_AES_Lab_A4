#include <ArduinoMqttClient.h>
#include <WiFiNINA.h>


#define MICROPHONE_PIN A0

char ssid[] = "AndreySysoev";
char pass[] = "12345678";


WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "broker.hivemq.com";
int port = 1883;

const char topic[] = "sensor/ky-037/microphone/data";

const long interval = 5000;
unsigned long previousMillis = 0;

// Sensor Specific variable
int rawValue;
int signalMin;
int signalMax;
int amplitude;
int noisePercentage;

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


    // Sensor specific limits
    signalMin = 1023;
    signalMax = 0;

    unsigned long startMillis = millis();

    while (millis() - startMillis < 50) {
      rawValue = analogRead(MICROPHONE_PIN);

      if (rawValue < signalMin) {
        signalMin = rawValue;
      }

      if (rawValue > signalMax) {
        signalMax = rawValue;
      }
    }

    amplitude = signalMax - signalMin;
    noisePercentage = map(amplitude, 0, 20, 0, 100);
    noisePercentage = constrain(noisePercentage, 0, 100);


    mqttClient.beginMessage(topic);

    mqttClient.print("{\"noise\":");
    mqttClient.print(noisePercentage);
    mqttClient.print("}");

    mqttClient.endMessage();

    Serial.print("Noise: ");
    Serial.print(noisePercentage);
    Serial.println("%");

    Serial.print("Data sent to topic: ");
    Serial.println(topic);
    Serial.println();
  }
}