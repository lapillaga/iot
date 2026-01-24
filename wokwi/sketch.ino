/*
 * Sistema IoT de Riego Inteligente para Pastizales
 * Trabajo Fin de Materia - IA aplicada a la industria 4.0
 *
 * VERSIÓN CORREGIDA - Envío automático cada 5 segundos
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <ArduinoJson.h>

// ============== PINES ==============
#define DHT_PIN 15
#define SOIL_MOISTURE_PIN 34
#define LED_VALVULA_ON 2
#define LED_VALVULA_OFF 4

// ============== WIFI (Wokwi) ==============
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// ============== HIVEMQ CLOUD ==============
const char* mqtt_server = "3f53469d473648f8a48abff7da04d106.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "admin";
const char* mqtt_password = "Luis1234567890";  // ← CAMBIA ESTO

// ============== TOPICS MQTT ==============
#define TOPIC_SENSORES    "pastizal/sensores"
#define TOPIC_VALVULA     "pastizal/valvula/estado"
#define TOPIC_CONTROL     "pastizal/valvula/control"
#define TOPIC_PREDICCION  "pastizal/prediccion"

// ============== OBJETOS ==============
DHTesp dht;
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ============== VARIABLES ==============
unsigned long lastMsg = 0;
const long interval = 3000;  // 3 segundos
bool valvulaAbierta = false;

// Variables para simular cambios graduales
float humedadSueloBase = 50.0;
unsigned long lastSimUpdate = 0;

// ============== CONECTAR WIFI ==============
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("🔄 Conectando a WiFi: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 40) {
    delay(500);
    Serial.print(".");
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi conectado!");
    Serial.print("   IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("❌ Error al conectar WiFi");
  }
}

// ============== CALLBACK MQTT ==============
void callback(char* topic, byte* payload, unsigned int length) {
  String mensaje = "";
  for (int i = 0; i < length; i++) {
    mensaje += (char)payload[i];
  }

  Serial.print("📩 Mensaje [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(mensaje);

  if (String(topic) == TOPIC_CONTROL) {
    if (mensaje == "ON" || mensaje == "1") {
      abrirValvula();
    } else if (mensaje == "OFF" || mensaje == "0") {
      cerrarValvula();
    }
  }

  if (String(topic) == TOPIC_PREDICCION) {
    if (mensaje == "REGAR") {
      Serial.println("🤖 ML dice: REGAR");
      abrirValvula();
    } else if (mensaje == "NO_REGAR") {
      Serial.println("🤖 ML dice: NO REGAR");
      cerrarValvula();
    }
  }
}

// ============== CONTROL VÁLVULA ==============
void abrirValvula() {
  valvulaAbierta = true;
  digitalWrite(LED_VALVULA_ON, HIGH);
  digitalWrite(LED_VALVULA_OFF, LOW);
  Serial.println("🚿 VÁLVULA ABIERTA");
  client.publish(TOPIC_VALVULA, "ON");
}

void cerrarValvula() {
  valvulaAbierta = false;
  digitalWrite(LED_VALVULA_ON, LOW);
  digitalWrite(LED_VALVULA_OFF, HIGH);
  Serial.println("🔴 VÁLVULA CERRADA");
  client.publish(TOPIC_VALVULA, "OFF");
}

// ============== CONECTAR MQTT ==============
void reconnect() {
  int intentos = 0;
  while (!client.connected() && intentos < 3) {
    Serial.print("🔄 Conectando a HiveMQ Cloud...");

    String clientId = "ESP32_Riego_" + String(random(0xffff), HEX);

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println(" ✅ Conectado!");
      client.subscribe(TOPIC_CONTROL);
      client.subscribe(TOPIC_PREDICCION);
      Serial.println("📡 Suscrito a topics de control");
    } else {
      Serial.print(" ❌ Error: ");
      Serial.println(client.state());
      delay(2000);
      intentos++;
    }
  }
}

// ============== LEER Y PUBLICAR SENSORES ==============
void publicarSensores() {
  // Leer DHT22
  TempAndHumidity data = dht.getTempAndHumidity();
  float temperatura = data.temperature;
  float humedadAmbiente = data.humidity;

  // Leer potenciómetro (simula humedad suelo)
  int valorAnalogico = analogRead(SOIL_MOISTURE_PIN);
  float humedadSuelo = map(valorAnalogico, 0, 4095, 0, 100);

  // Si la válvula está abierta, simular que sube la humedad
  if (valvulaAbierta && humedadSuelo < 90) {
    humedadSuelo += 2;  // Sube un poco al regar
  }

  // Crear JSON
  StaticJsonDocument<256> doc;
  doc["humedad_suelo"] = humedadSuelo;
  doc["temperatura"] = temperatura;
  doc["humedad_ambiente"] = humedadAmbiente;
  doc["valvula"] = valvulaAbierta ? "ON" : "OFF";
  doc["timestamp"] = millis() / 1000;

  char buffer[256];
  serializeJson(doc, buffer);

  // Publicar
  bool publicado = client.publish(TOPIC_SENSORES, buffer);

  // Mostrar en serial
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.print("📊 [");
  Serial.print(millis() / 1000);
  Serial.println("s] DATOS ENVIADOS:");
  Serial.print("   🌱 Humedad Suelo:  ");
  Serial.print(humedadSuelo, 1);
  Serial.println(" %");
  Serial.print("   🌡️  Temperatura:    ");
  Serial.print(temperatura, 1);
  Serial.println(" °C");
  Serial.print("   💧 Humedad Amb:    ");
  Serial.print(humedadAmbiente, 1);
  Serial.println(" %");
  Serial.print("   🚿 Válvula:        ");
  Serial.println(valvulaAbierta ? "ABIERTA" : "CERRADA");
  Serial.print("   📤 Publicado:      ");
  Serial.println(publicado ? "✅ OK" : "❌ ERROR");
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
}

// ============== SETUP ==============
void setup() {
  Serial.begin(115200);
  delay(1000);  // Dar tiempo a Wokwi

  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║  Sistema IoT Riego Inteligente     ║");
  Serial.println("║  UTPL - Maestría IA                ║");
  Serial.println("║  Envío automático cada 5 seg       ║");
  Serial.println("╚════════════════════════════════════╝\n");

  // Pines
  pinMode(LED_VALVULA_ON, OUTPUT);
  pinMode(LED_VALVULA_OFF, OUTPUT);

  // Estado inicial
  cerrarValvula();

  // DHT22
  dht.setup(DHT_PIN, DHTesp::DHT22);

  // WiFi
  setup_wifi();

  // MQTT con TLS
  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  client.setKeepAlive(60);
  client.setSocketTimeout(30);

  // Conectar MQTT inmediatamente
  reconnect();

  // Publicar primer dato inmediatamente
  if (client.connected()) {
    publicarSensores();
  }

  Serial.println("✅ Sistema listo - enviando datos cada 5 segundos\n");
}

// ============== LOOP ==============
void loop() {
  // Mantener conexión MQTT
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Publicar cada 5 segundos (sin importar si hay cambios)
  unsigned long now = millis();
  if (now - lastMsg >= interval) {
    lastMsg = now;

    if (client.connected()) {
      publicarSensores();
    } else {
      Serial.println("⚠️ MQTT desconectado, reintentando...");
    }
  }

  // Pequeño delay para que Wokwi no pause el loop
  delay(100);
}
