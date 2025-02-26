#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "vivo Y33T";
const char* password = "ashantha";
const char* mqtt_broker = "192.168.52.106";
const int mqtt_port = 1883;
const char* topic = "test/topic";

WiFiClient espClient;                      
PubSubClient client(espClient);

// LED pins for IR1 and IR2                
const int LED_IR1_DETECTED = 2;
const int LED_IR1_NOT_DETECTED = 15;
const int LED_IR2_DETECTED = 18;
const int LED_IR2_NOT_DETECTED = 19;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);

  // Set up LED pins
  pinMode(LED_IR1_DETECTED, OUTPUT);
  pinMode(LED_IR1_NOT_DETECTED, OUTPUT);
  pinMode(LED_IR2_DETECTED, OUTPUT);
  pinMode(LED_IR2_NOT_DETECTED, OUTPUT);
}

void callback(char* topic, byte* payload, unsigned int length) {
  payload[length] = '\0'; // Null-terminate the payload
  String message = String((char*)payload); // Convert payload to a string
  message.trim(); // Trim extra spaces and newlines

  Serial.print("Message: ");
  Serial.println(message);

  // Split the message at the comma
  int commaIndex = message.indexOf(',');

  if (commaIndex != -1) {
    String ir1_status = message.substring(0, commaIndex); // Part before comma for IR1
    String ir2_status = message.substring(commaIndex + 1); // Part after comma for IR2

    ir1_status.trim(); // Trim any spaces
    ir2_status.trim(); // Trim any spaces

    // Control LEDs for IR1
    if (ir1_status == "IR1: Detected") {
      digitalWrite(LED_IR1_DETECTED, HIGH);
      digitalWrite(LED_IR1_NOT_DETECTED, LOW);
    } else if (ir1_status == "IR1: Not detected") {
      digitalWrite(LED_IR1_DETECTED, LOW);
      digitalWrite(LED_IR1_NOT_DETECTED, HIGH);
    }

    // Control LEDs for IR2
    if (ir2_status == "IR2: Detected") {
      digitalWrite(LED_IR2_DETECTED, HIGH);
      digitalWrite(LED_IR2_NOT_DETECTED, LOW);
    } else if (ir2_status == "IR2: Not detected") {
      digitalWrite(LED_IR2_DETECTED, LOW);
      digitalWrite(LED_IR2_NOT_DETECTED, HIGH);
    }
  }
}

void loop() {
  if (!client.connected()) {
    if (client.connect("ESP32Client")) {
      client.subscribe(topic);
    }
  }
  client.loop();
}