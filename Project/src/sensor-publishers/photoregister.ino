#include <ArduinoMqttClient.h>
#include <WiFi.h>


#define RESISTOR_PIN 34

char ssid[] = "AndreySysoev";
char pass[] = "12345678";


WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "broker.hivemq.com";
int port = 1883;

const char topic[] = "sensor/ky-018/photoresistor/data";

const long interval = 5000;
unsigned long previousMillis = 0;

// Sensor Specific variable
int rawValue;
int brightness;

void setup() {
  Serial.begin(9600);
  delay(1000);

  Serial.println();
  Serial.println("ESP32 KY-018 Photoresistor MQTT Publisher");
  Serial.println();

  pinMode(RESISTOR_PIN, INPUT);

  Serial.print("Attempting to connect to SSID: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(1000);

  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

  Serial.println();
  Serial.println("You're connected to the network");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
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

    // ESP32 analog range is 0 - 4095
    brightness = map(rawValue, 0, 4095, 0, 100);
    brightness = constrain(brightness, 0, 100);


    mqttClient.beginMessage(topic);

    mqttClient.print("{\"brightness\":");
    mqttClient.print(brightness);
    mqttClient.print("}");

    mqttClient.endMessage();

    Serial.print("Raw value: ");
    Serial.println(rawValue);

    Serial.print("Brightness: ");
    Serial.print(brightness);
    Serial.println("%");

    Serial.print("Data sent to topic: ");
    Serial.println(topic);
    Serial.println();
  }
}