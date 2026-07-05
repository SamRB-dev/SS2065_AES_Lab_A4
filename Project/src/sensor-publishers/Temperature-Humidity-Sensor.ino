#include <ArduinoMqttClient.h>
#include <WiFiNINA.h>
#include <DHT.h>


#define DHTPIN 2
#define DHTTYPE DHT11

char ssid[] = "AndreySysoev";
char pass[] = "12345678";

DHT dht(DHTPIN, DHTTYPE);

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "broker.hivemq.com";
int port = 1883;

const char topic[] = "sensor/ky-015/temperature-humidity/data";

const long interval = 5000;
unsigned long previousMillis = 0;

// Sensor Specific variable
float temperature;
float humidity;

void setup() {
  Serial.begin(9600);
  dht.begin();

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
    temperature = dht.readTemperature();
    humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT11 sensor!");
      return;
    }


    mqttClient.beginMessage(topic);

    mqttClient.print("{\"temperature\":");
    mqttClient.print(temperature);
    mqttClient.print(",\"humidity\":");
    mqttClient.print(humidity);
    mqttClient.print("}");

    mqttClient.endMessage();

    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");

    Serial.print("Data sent to topic: ");
    Serial.println(topic);
    Serial.println();
  }
}