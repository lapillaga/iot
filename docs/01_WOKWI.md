# 01 - Configuracion de Wokwi (Simulador ESP32)

## Que es Wokwi?

Wokwi es un simulador online de microcontroladores que permite probar codigo Arduino/ESP32 **sin necesidad de hardware fisico**. Simula WiFi, sensores, LEDs y conexion MQTT.

**URL:** https://wokwi.com

---

## Diagrama del Circuito

```
                        +-------------------------+
                        |         ESP32           |
                        |      DevKit C V4        |
                        |                         |
    +--------+          |                         |          +--------+
    | DHT22  |---[DATA]-|---> GPIO 15             |          |        |
    | Sensor |---[VCC]--|---> 3V3                 |          |        |
    | Temp/  |---[GND]--|---> GND                 |          |        |
    | Humid  |          |                         |          |        |
    +--------+          |                         |          |        |
                        |                         |          |        |
    +--------+          |                         |          |        |
    | POT    |---[SIG]--|---> GPIO 34 (ADC)       |          |        |
    | 10k    |---[VCC]--|---> 3V3                 |          | Serial |
    | (Suelo)|---[GND]--|---> GND                 |          | Monitor|
    +--------+          |                         |          |        |
                        |                         |          |        |
    +--------+          |                         |          |        |
    | LED    |---[+]----|---> GPIO 2 (via R 220)  |---[TX]---|        |
    | Verde  |---[-]----|---> GND                 |---[RX]---|        |
    | (ON)   |          |                         |          |        |
    +--------+          |                         |          +--------+
                        |                         |
    +--------+          |                         |
    | LED    |---[+]----|---> GPIO 4 (via R 220)  |
    | Rojo   |---[-]----|---> GND                 |
    | (OFF)  |          |                         |
    +--------+          +-------------------------+
                                   |
                                   | WiFi
                                   v
                        +-------------------+
                        |    Wokwi-GUEST    |
                        |    (Internet)     |
                        +-------------------+
                                   |
                                   v
                        +-------------------+
                        |   HiveMQ Cloud    |
                        |   (MQTT Broker)   |
                        +-------------------+
```

---

## Paso a Paso

### Paso 1: Crear Proyecto en Wokwi

1. Ir a https://wokwi.com
2. Click en **"Start a new project"**
3. Seleccionar **"ESP32"**
4. Se abrira el editor con un proyecto vacio

---

### Paso 2: Configurar diagram.json

En la pestana **diagram.json**, reemplazar todo el contenido con:

```json
{
  "version": 1,
  "author": "Luis - UTPL",
  "editor": "wokwi",
  "parts": [
    {
      "type": "board-esp32-devkit-c-v4",
      "id": "esp",
      "top": 0,
      "left": 100,
      "attrs": {}
    },
    {
      "type": "wokwi-dht22",
      "id": "dht1",
      "top": -100,
      "left": 20,
      "attrs": { "temperature": "25", "humidity": "60" }
    },
    {
      "type": "wokwi-potentiometer",
      "id": "pot1",
      "top": -100,
      "left": 300,
      "attrs": { "value": "50" }
    },
    {
      "type": "wokwi-led",
      "id": "led1",
      "top": 150,
      "left": 50,
      "attrs": { "color": "green" }
    },
    {
      "type": "wokwi-led",
      "id": "led2",
      "top": 150,
      "left": 120,
      "attrs": { "color": "red" }
    },
    {
      "type": "wokwi-resistor",
      "id": "r1",
      "top": 200,
      "left": 40,
      "attrs": { "value": "220" }
    },
    {
      "type": "wokwi-resistor",
      "id": "r2",
      "top": 200,
      "left": 110,
      "attrs": { "value": "220" }
    }
  ],
  "connections": [
    [ "esp:TX", "$serialMonitor:RX", "", [] ],
    [ "esp:RX", "$serialMonitor:TX", "", [] ],
    [ "dht1:VCC", "esp:3V3", "red", [ "v:0" ] ],
    [ "dht1:SDA", "esp:15", "green", [ "v:0" ] ],
    [ "dht1:GND", "esp:GND.1", "black", [ "v:0" ] ],
    [ "pot1:VCC", "esp:3V3", "red", [ "v:0" ] ],
    [ "pot1:SIG", "esp:34", "orange", [ "v:0" ] ],
    [ "pot1:GND", "esp:GND.2", "black", [ "v:0" ] ],
    [ "led1:A", "r1:1", "", [] ],
    [ "r1:2", "esp:2", "green", [] ],
    [ "led1:C", "esp:GND.1", "black", [] ],
    [ "led2:A", "r2:1", "", [] ],
    [ "r2:2", "esp:4", "red", [] ],
    [ "led2:C", "esp:GND.2", "black", [] ]
  ],
  "dependencies": {}
}
```

---

### Paso 3: Configurar libraries.txt

Crear archivo **libraries.txt** con:

```
# Wokwi Library List
# See https://docs.wokwi.com/guides/libraries

PubSubClient
DHT sensor library for ESPx
ArduinoJson
```

---

### Paso 4: Copiar Codigo sketch.ino

En la pestana **sketch.ino**, copiar el codigo del archivo `wokwi/sketch.ino` del proyecto.

**IMPORTANTE:** Antes de ejecutar, verifica las credenciales MQTT:

```cpp
// Linea 25-28 del sketch.ino
const char* mqtt_server = "TU_SERVIDOR.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "TU_USUARIO";
const char* mqtt_password = "TU_PASSWORD";
```

Estas credenciales las obtendras en el paso `02_HIVEMQ.md`.

---

### Paso 5: Ejecutar Simulacion

1. Click en el boton verde **"Start the simulation"** (Play)
2. Abrir el **Serial Monitor** (icono de terminal)
3. Deberias ver:

```
╔════════════════════════════════════╗
║  Sistema IoT Riego Inteligente     ║
║  UTPL - Maestria IA                ║
║  Envio automatico cada 3 seg       ║
╚════════════════════════════════════╝

🔄 Conectando a WiFi: Wokwi-GUEST
.....
✅ WiFi conectado!
   IP: 10.10.0.2

🔄 Conectando a HiveMQ Cloud... ✅ Conectado!
📡 Suscrito a topics de control

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 [3s] DATOS ENVIADOS:
   🌱 Humedad Suelo:  50.0 %
   🌡️  Temperatura:    25.0 °C
   💧 Humedad Amb:    60.0 %
   🚿 Valvula:        CERRADA
   📤 Publicado:      ✅ OK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Interaccion con el Simulador

### Cambiar Humedad del Suelo
- Girar el **potenciometro** (POT) para simular diferentes niveles de humedad
- Valor 0% = Suelo muy seco
- Valor 100% = Suelo saturado

### Cambiar Temperatura/Humedad Ambiente
- Click en el **sensor DHT22**
- Modificar los valores de temperatura y humedad

### Ver Estado de Valvula
- **LED Verde encendido** = Valvula ABIERTA (regando)
- **LED Rojo encendido** = Valvula CERRADA (sin regar)

---

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| WiFi no conecta | Normal en Wokwi, esperar ~10 segundos |
| MQTT error -2 | Verificar URL del broker HiveMQ |
| MQTT error -4 | Verificar usuario/password |
| No publica datos | Verificar que MQTT este conectado |

---

## Archivos del Proyecto

Los archivos necesarios estan en la carpeta `wokwi/`:

```
wokwi/
├── sketch.ino      # Codigo principal
├── diagram.json    # Configuracion del circuito
└── libraries.txt   # Librerias necesarias
```

---

## Siguiente Paso

Continuar con `02_HIVEMQ.md` para configurar el broker MQTT en la nube.
