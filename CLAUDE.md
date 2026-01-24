# 🌱 Sistema IoT Inteligente para Riego de Pastizales Ganaderos

## Trabajo Fin de Materia - IA Aplicada a la Industria 4.0
**Universidad:** UTPL - Maestría en Inteligencia Artificial Aplicada  
**Autor:** Luis  
**Fecha:** Enero 2026

---

## 📋 Índice

1. [Descripción del Proyecto](#1-descripción-del-proyecto)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Componentes Detallados](#3-componentes-detallados)
4. [Flujo de Datos](#4-flujo-de-datos)
5. [Configuración Paso a Paso](#5-configuración-paso-a-paso)
6. [Modelo de Machine Learning](#6-modelo-de-machine-learning)
7. [API Climática (Open-Meteo)](#7-api-climática-open-meteo)
8. [Base de Datos (InfluxDB)](#8-base-de-datos-influxdb)
9. [Visualización (Grafana)](#9-visualización-grafana)
10. [Código Fuente](#10-código-fuente)
11. [Próximos Pasos](#11-próximos-pasos)

---

## 1. Descripción del Proyecto

### 1.1 Contexto y Problema

En zonas rurales de la sierra ecuatoriana (específicamente Paute, Azuay), los pastizales para ganadería sufren de:
- **Sequías estacionales** que vuelven los pastos amarillos
- **Falta de sistemas de riego automatizado**
- **Desperdicio de agua** por riego manual sin criterio técnico
- **Pérdida económica** por pastos de baja calidad

### 1.2 Solución Propuesta

Un **Sistema IoT Inteligente** que:
1. **Monitorea** en tiempo real las condiciones del suelo y ambiente
2. **Predice** la necesidad de riego usando Machine Learning
3. **Integra** datos climáticos (pronóstico de lluvia)
4. **Automatiza** la decisión de regar o no regar
5. **Visualiza** toda la información en dashboards

### 1.3 Diferenciadores Clave

| Sistemas Tradicionales | Este Sistema |
|------------------------|--------------|
| Reglas simples: "si humedad < 30%, regar" | ML predictivo con múltiples variables |
| Solo datos locales | Integración con API climática |
| Sin histórico | Base de datos temporal (InfluxDB) |
| Sin visualización | Dashboard en tiempo real (Grafana) |

### 1.4 Objetivos

- **Reducir consumo de agua** hasta 30% evitando riegos innecesarios
- **Mejorar calidad del pasto** con riego óptimo
- **Automatizar decisiones** basadas en datos y predicciones
- **Demostrar** aplicación de IoT + ML en agricultura

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ARQUITECTURA DEL SISTEMA                             │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │   WOKWI     │  MQTT   │   HiveMQ    │  MQTT   │  NODE-RED   │
    │  (ESP32)    │────────▶│   Cloud     │────────▶│  (Local)    │
    │  Sensores   │   TLS   │   Broker    │   TLS   │  Procesador │
    └─────────────┘         └─────────────┘         └──────┬──────┘
          ▲                                                │
          │                                                │
          │ Control                          ┌─────────────┼─────────────┐
          │ Válvula                          │             │             │
          │                                  ▼             ▼             ▼
    ┌─────┴─────┐                     ┌───────────┐ ┌───────────┐ ┌───────────┐
    │   LEDs    │                     │ Open-Meteo│ │ InfluxDB  │ │  Modelo   │
    │ (Válvula) │                     │    API    │ │   Cloud   │ │    ML     │
    └───────────┘                     │  (Clima)  │ │   (BD)    │ │ (Python)  │
                                      └───────────┘ └─────┬─────┘ └───────────┘
                                                          │
                                                          ▼
                                                   ┌───────────┐
                                                   │  GRAFANA  │
                                                   │  Cloud    │
                                                   │(Dashboard)│
                                                   └───────────┘
```

### 2.2 Stack Tecnológico

| Capa | Tecnología | Función | Costo |
|------|------------|---------|-------|
| **Simulación** | Wokwi | Simular ESP32 + sensores | Gratis |
| **Comunicación** | HiveMQ Cloud | Broker MQTT con TLS | Gratis (plan free) |
| **Procesamiento** | Node-RED | Orquestación y lógica | Gratis (local) |
| **Datos Climáticos** | Open-Meteo API | Pronóstico del tiempo | Gratis |
| **Base de Datos** | InfluxDB Cloud | Almacenamiento temporal | Gratis (plan free) |
| **Visualización** | Grafana Cloud | Dashboards | Gratis (plan free) |
| **ML** | Python + scikit-learn | Modelo predictivo | Gratis |

### 2.3 Protocolos Utilizados

- **MQTT** (Message Queuing Telemetry Transport): Comunicación IoT ligera
- **TLS/SSL**: Cifrado de comunicaciones (puerto 8883)
- **HTTP/REST**: Consultas a Open-Meteo API
- **Flux/SQL**: Consultas a InfluxDB

---

## 3. Componentes Detallados

### 3.1 Wokwi - Simulador de Hardware

#### ¿Qué es?
Wokwi es un simulador online de microcontroladores que permite probar código Arduino/ESP32 sin hardware físico.

#### Hardware Simulado

| Componente | Modelo | Función | Pin |
|------------|--------|---------|-----|
| Microcontrolador | ESP32 DevKit | Procesamiento + WiFi | - |
| Sensor Temp/Hum | DHT22 | Medir temperatura y humedad ambiente | GPIO 15 |
| Potenciómetro | 10kΩ | Simular sensor de humedad del suelo | GPIO 34 (ADC) |
| LED Verde | 5mm | Indicar válvula ABIERTA | GPIO 2 |
| LED Rojo | 5mm | Indicar válvula CERRADA | GPIO 4 |
| Resistencias | 220Ω | Protección de LEDs | - |

#### Diagrama del Circuito

```
                    ┌─────────────────────┐
                    │      ESP32          │
                    │                     │
    DHT22 ──────────┤ GPIO 15             │
                    │                     │
    Potenciómetro ──┤ GPIO 34 (ADC)       │
                    │                     │
    LED Verde ──────┤ GPIO 2              │
                    │                     │
    LED Rojo ───────┤ GPIO 4              │
                    │                     │
                    │        WiFi         │──────▶ Internet
                    └─────────────────────┘
```

#### Librerías Utilizadas

```cpp
#include <WiFi.h>              // Conexión WiFi
#include <WiFiClientSecure.h>  // Conexión TLS
#include <PubSubClient.h>      // Cliente MQTT
#include <DHTesp.h>            // Sensor DHT22
#include <ArduinoJson.h>       // Serialización JSON
```

---

### 3.2 HiveMQ Cloud - Broker MQTT

#### ¿Qué es?
HiveMQ Cloud es un broker MQTT gestionado en la nube que permite comunicación pub/sub entre dispositivos IoT.

#### Configuración

| Parámetro | Valor |
|-----------|-------|
| **URL** | 3f53469d473648f8a48abff7da04d106.s1.eu.hivemq.cloud |
| **Puerto TLS** | 8883 |
| **Puerto WebSocket** | 8884 |
| **Usuario** | admin |
| **Protocolo** | MQTT v4 |

#### Topics MQTT

| Topic | Dirección | Descripción |
|-------|-----------|-------------|
| `pastizal/sensores` | ESP32 → Node-RED | Datos de sensores (JSON) |
| `pastizal/valvula/estado` | ESP32 → Node-RED | Estado actual de válvula |
| `pastizal/valvula/control` | Node-RED → ESP32 | Comando manual (ON/OFF) |
| `pastizal/prediccion` | Node-RED → ESP32 | Decisión del ML (REGAR/NO_REGAR) |

#### Estructura del Mensaje (sensores)

```json
{
  "humedad_suelo": 45.2,
  "temperatura": 23.5,
  "humedad_ambiente": 68.0,
  "valvula": "OFF",
  "timestamp": 12345
}
```

---

### 3.3 Node-RED - Orquestador

#### ¿Qué es?
Node-RED es una herramienta de programación visual basada en flujos, ideal para IoT.

#### Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO NODE-RED                                    │
└─────────────────────────────────────────────────────────────────────────────┘

SENSORES:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ MQTT In      │───▶│ Procesar     │───▶│ Debug        │    │              │
│ (sensores)   │    │ datos        │    │ (ver datos)  │    │              │
└──────────────┘    └──────┬───────┘    └──────────────┘    │              │
                           │                                 │              │
                           ▼                                 │              │
                    ┌──────────────┐    ┌──────────────┐    │              │
                    │ Preparar     │───▶│ InfluxDB     │    │              │
                    │ para Influx  │    │ (guardar)    │    │              │
                    └──────────────┘    └──────────────┘    │              │
                                                            │              │
CLIMA:                                                      │              │
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │              │
│ Inject       │───▶│ HTTP Request │───▶│ Procesar     │───▶│ InfluxDB    │
│ (cada 30min) │    │ (Open-Meteo) │    │ clima        │    │ (guardar)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

DECISIÓN ML:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Inject       │───▶│ Modelo ML    │───▶│ Switch       │───▶│ MQTT Out    │
│ (cada 1min)  │    │ (decisión)   │    │ (¿regar?)    │    │ (a ESP32)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

CONTROL MANUAL:
┌──────────────┐
│ Inject ON    │───┐
└──────────────┘   │    ┌──────────────┐
                   ├───▶│ MQTT Out     │
┌──────────────┐   │    │ (control)    │
│ Inject OFF   │───┘    └──────────────┘
└──────────────┘
```

#### Nodos Instalados

```bash
# Instalar desde Node-RED → Manage Palette
node-red-contrib-influxdb
node-red-dashboard  # (opcional, para UI local)
```

---

## 4. Flujo de Datos

### 4.1 Flujo Completo (Paso a Paso)

```
PASO 1: CAPTURA DE DATOS
────────────────────────
[Wokwi] DHT22 mide temperatura: 23.5°C
[Wokwi] DHT22 mide humedad ambiente: 68%
[Wokwi] Potenciómetro simula humedad suelo: 45%

        │
        ▼

PASO 2: ENVÍO MQTT
──────────────────
[Wokwi] Serializa datos a JSON
[Wokwi] Publica en topic "pastizal/sensores"
[Wokwi] Conexión TLS al broker HiveMQ (puerto 8883)

        │
        ▼

PASO 3: BROKER MQTT
───────────────────
[HiveMQ] Recibe mensaje
[HiveMQ] Distribuye a todos los suscriptores

        │
        ▼

PASO 4: PROCESAMIENTO NODE-RED
──────────────────────────────
[Node-RED] Recibe datos via MQTT
[Node-RED] Extrae valores del JSON
[Node-RED] Guarda en contexto de flujo

        │
        ├─────────────────────────────────┐
        ▼                                 ▼

PASO 5A: ALMACENAMIENTO              PASO 5B: CONSULTA CLIMA
────────────────────────             ───────────────────────
[Node-RED] Formatea para InfluxDB    [Node-RED] Llama Open-Meteo API
[InfluxDB] Almacena con timestamp    [Open-Meteo] Retorna pronóstico
                                     [Node-RED] Extrae prob. lluvia 24h

        │                                 │
        └────────────────┬────────────────┘
                         ▼

PASO 6: DECISIÓN ML
───────────────────
[Node-RED] Combina: sensores + clima + hora
[Node-RED] Ejecuta modelo de decisión
[Node-RED] Resultado: REGAR o NO_REGAR

        │
        ▼

PASO 7: ACTUACIÓN
─────────────────
[Node-RED] Publica decisión en "pastizal/prediccion"
[HiveMQ] Distribuye al ESP32
[Wokwi] Recibe comando
[Wokwi] Abre/cierra válvula (LEDs)

        │
        ▼

PASO 8: VISUALIZACIÓN
─────────────────────
[Grafana] Consulta InfluxDB
[Grafana] Muestra dashboards en tiempo real
```

### 4.2 Tiempos de Actualización

| Proceso | Intervalo | Justificación |
|---------|-----------|---------------|
| Envío sensores | 5 segundos | Balance entre precisión y consumo |
| Consulta clima | 30 minutos | El clima no cambia rápido |
| Decisión ML | 1 minuto | Suficiente para detectar cambios |
| Dashboard | Tiempo real | Streaming de InfluxDB |

---

## 5. Configuración Paso a Paso

### 5.1 Prerequisitos

- Navegador web moderno
- Node.js instalado (para Node-RED local)
- Cuentas gratuitas en: HiveMQ, InfluxDB Cloud, Grafana Cloud

### 5.2 Paso 1: Configurar HiveMQ Cloud

1. Ir a https://www.hivemq.com/cloud/
2. Crear cuenta gratuita
3. Crear cluster (Serverless Free)
4. Crear credenciales:
   - Username: `admin`
   - Password: `[tu-password]`
5. Anotar URL del cluster: `xxx.s1.eu.hivemq.cloud`

### 5.3 Paso 2: Configurar Node-RED

```bash
# Instalar Node-RED
npm install -g --unsafe-perm node-red

# Ejecutar
node-red

# Abrir en navegador
http://localhost:1880
```

Instalar nodos adicionales:
- Menu → Manage Palette → Install
- Buscar e instalar: `node-red-contrib-influxdb`

### 5.4 Paso 3: Configurar InfluxDB Cloud

1. Ir a https://cloud2.influxdata.com/signup
2. Crear cuenta gratuita
3. Crear bucket: `riego_iot`
4. Generar API Token (All Access)
5. Anotar: URL, Organization ID, Token

### 5.5 Paso 4: Configurar Wokwi

1. Ir a https://wokwi.com
2. Crear nuevo proyecto ESP32
3. Copiar código de `sketch.ino`
4. Copiar diagrama de `diagram.json`
5. Agregar librerías: PubSubClient, DHT sensor library for ESPx, ArduinoJson
6. Editar credenciales MQTT en el código

### 5.6 Paso 5: Configurar Grafana Cloud

1. Ir a https://grafana.com/products/cloud/
2. Crear cuenta gratuita
3. Agregar Data Source → InfluxDB
4. Configurar conexión con credenciales de InfluxDB
5. Crear dashboard con paneles

---

## 6. Modelo de Machine Learning

### 6.1 Estado Actual: Sistema Basado en Reglas

Actualmente el sistema usa reglas if/else como placeholder:

```javascript
// REGLA 1: Suelo muy seco = regar urgente
if (humedad_suelo < 20) {
    decision = "REGAR";
    razon = "Suelo crítico";
}
// REGLA 2: Suelo seco pero va a llover = esperar
else if (humedad_suelo < 35 && prob_lluvia > 70) {
    decision = "NO_REGAR";
    razon = "Esperar lluvia";
}
// REGLA 3: Suelo seco + calor + no lluvia = regar
else if (humedad_suelo < 40 && temperatura > 25 && prob_lluvia < 40) {
    decision = "REGAR";
    razon = "Seco + calor + sin lluvia";
}
// ... más reglas
```

**Limitación:** Esto NO es Machine Learning, son reglas programadas manualmente.

### 6.2 Plan: Modelo ML Real

#### Enfoque Propuesto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODELO ML PROPUESTO                                  │
└─────────────────────────────────────────────────────────────────────────────┘

DATOS DE ENTRENAMIENTO:
───────────────────────
• Datos históricos de clima de Paute (Open-Meteo Historical API)
• Periodo: 2020-2024 (5 años)
• Variables: temperatura, humedad, precipitación, humedad suelo estimada

        │
        ▼

GENERACIÓN DE ETIQUETAS:
────────────────────────
• Basadas en criterios agronómicos para pastizales
• Literatura científica sobre riego en sierra andina
• Reglas expertas validadas

        │
        ▼

ENTRENAMIENTO:
──────────────
• Algoritmo: Random Forest o KNN
• Framework: scikit-learn (Python)
• Métricas: Accuracy, Precision, Recall, F1-Score

        │
        ▼

DESPLIEGUE:
───────────
• API Flask local
• Node-RED consume la API
• Predicción en tiempo real
```

#### Variables de Entrada (Features)

| Variable | Fuente | Tipo | Rango |
|----------|--------|------|-------|
| humedad_suelo | Sensor local | float | 0-100% |
| temperatura | Sensor local | float | 0-50°C |
| humedad_ambiente | Sensor local | float | 0-100% |
| prob_lluvia_24h | Open-Meteo | float | 0-100% |
| temp_max_mañana | Open-Meteo | float | 0-50°C |
| precipitacion_ayer | Open-Meteo | float | 0-100mm |
| hora_del_dia | Sistema | int | 0-23 |
| mes | Sistema | int | 1-12 |

#### Variable de Salida (Target)

| Valor | Significado |
|-------|-------------|
| 0 | NO_REGAR |
| 1 | REGAR |

#### Justificación del Algoritmo

**Random Forest** es ideal porque:
- Maneja bien variables numéricas y categóricas
- Robusto contra overfitting
- Permite ver importancia de variables
- Fácil de interpretar
- Papers reportan ~95% accuracy en problemas similares

---

## 7. API Climática (Open-Meteo)

### 7.1 ¿Por qué Open-Meteo?

| Característica | Open-Meteo | Otras APIs |
|----------------|------------|------------|
| **Costo** | Gratis | Pago o limitado |
| **API Key** | No requiere | Requiere |
| **Datos históricos** | Desde 1940 | Limitado |
| **Pronóstico** | Hasta 16 días | Variable |
| **Humedad suelo** | ✅ Disponible | Raro |

### 7.2 Endpoint Utilizado

```
https://api.open-meteo.com/v1/forecast
  ?latitude=-2.78
  &longitude=-78.76
  &current=temperature_2m,relative_humidity_2m,precipitation
  &hourly=precipitation_probability,soil_moisture_0_to_1cm
  &daily=precipitation_sum,precipitation_probability_max
  &timezone=America/Guayaquil
  &forecast_days=3
```

### 7.3 Variables Obtenidas

| Variable | Descripción | Uso |
|----------|-------------|-----|
| temperature_2m | Temperatura actual | Contexto |
| relative_humidity_2m | Humedad actual | Contexto |
| precipitation | Precipitación actual | Decisión |
| precipitation_probability | Prob. lluvia por hora | Decisión clave |
| soil_moisture_0_to_1cm | Humedad suelo estimada | Validación |
| precipitation_sum | Lluvia acumulada día | Histórico |

### 7.4 Coordenadas

```
Ubicación: Paute, Azuay, Ecuador
Latitud:   -2.78
Longitud:  -78.76
Timezone:  America/Guayaquil (UTC-5)
```

---

## 8. Base de Datos (InfluxDB)

### 8.1 ¿Por qué InfluxDB?

InfluxDB es una base de datos de **series temporales** optimizada para IoT:
- Almacena datos con timestamps automáticos
- Consultas optimizadas para rangos de tiempo
- Compresión eficiente
- Ideal para métricas y sensores

### 8.2 Estructura de Datos

#### Measurement: sensores_pastizal

| Campo | Tipo | Descripción |
|-------|------|-------------|
| time | timestamp | Automático |
| humedad_suelo | float | 0-100% |
| temperatura | float | °C |
| humedad_ambiente | float | 0-100% |
| valvula | int | 0=cerrada, 1=abierta |
| ubicacion (tag) | string | "paute" |
| dispositivo (tag) | string | "esp32_01" |

#### Measurement: clima_openmeteo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| time | timestamp | Automático |
| temp_actual | float | °C |
| humedad_actual | float | % |
| prob_lluvia_24h | float | % |
| precipitacion | float | mm |

#### Measurement: decisiones_riego

| Campo | Tipo | Descripción |
|-------|------|-------------|
| time | timestamp | Automático |
| decision | int | 0=no regar, 1=regar |
| confianza | float | % |
| humedad_suelo | float | % |
| temperatura | float | °C |
| prob_lluvia | float | % |

### 8.3 Queries SQL Útiles

```sql
-- Ver últimos datos de sensores
SELECT * 
FROM "sensores_pastizal" 
WHERE time >= now() - interval '1 hour'
ORDER BY time DESC
LIMIT 10;

-- Promedio de humedad por hora
SELECT 
  DATE_BIN(INTERVAL '1 hour', time, '2024-01-01T00:00:00Z') as hora,
  AVG(humedad_suelo) as humedad_promedio
FROM "sensores_pastizal"
WHERE time >= now() - interval '24 hours'
GROUP BY hora
ORDER BY hora;

-- Contar decisiones de riego
SELECT 
  decision,
  COUNT(*) as cantidad
FROM "decisiones_riego"
WHERE time >= now() - interval '24 hours'
GROUP BY decision;
```

---

## 9. Visualización (Grafana)

### 9.1 Dashboard Propuesto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🌱 Sistema de Riego IoT - Pastizales Paute                                 │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│                 │                 │                 │                       │
│  HUMEDAD SUELO  │  TEMPERATURA    │  VÁLVULA        │  PROB. LLUVIA 24H     │
│                 │                 │                 │                       │
│     ┌───┐       │     ┌───┐       │                 │      ┌───┐            │
│     │45%│       │     │23°│       │    CERRADA      │      │30%│            │
│     └───┘       │     └───┘       │      🔴         │      └───┘            │
│    [GAUGE]      │    [GAUGE]      │    [STAT]       │     [GAUGE]           │
│                 │                 │                 │                       │
├─────────────────┴─────────────────┴─────────────────┴───────────────────────┤
│                                                                             │
│  📈 HISTÓRICO DE SENSORES (última hora)                                     │
│  ════════════════════════════════════════════════════════════════════════   │
│  ╱╲    ╱╲                                                                   │
│ ╱  ╲  ╱  ╲  ────── Humedad suelo                                            │
│╱    ╲╱    ╲ ────── Temperatura                                              │
│            ────── Humedad ambiente                                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🤖 DECISIONES DEL MODELO ML (últimas 24h)                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ ██████████████████░░░░░░░░░░ │ REGAR: 12  │  NO_REGAR: 8            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Paneles Configurados

| Panel | Tipo | Query Flux |
|-------|------|------------|
| Humedad Suelo | Gauge | `filter _field == "humedad_suelo" \| last()` |
| Temperatura | Gauge | `filter _field == "temperatura" \| last()` |
| Válvula | Stat | `filter _field == "valvula" \| last()` |
| Prob. Lluvia | Gauge | `filter _measurement == "clima_openmeteo"` |
| Histórico | Time Series | `filter _measurement == "sensores_pastizal"` |

---

## 10. Código Fuente

### 10.1 Estructura de Archivos

```
proyecto_riego/
├── CLAUDE.md                    # Este documento
├── wokwi/
│   ├── sketch.ino              # Código ESP32
│   └── diagram.json            # Circuito Wokwi
├── nodered/
│   └── flujo_riego.json        # Flujo importable
├── python/                      # (Pendiente)
│   ├── entrenar_modelo.py
│   ├── api_flask.py
│   └── dataset/
└── docs/
    └── informe_final.docx      # (Pendiente)
```

### 10.2 Código ESP32 (Resumen)

```cpp
// Conexión
WiFi → Wokwi-GUEST (sin password)
MQTT → HiveMQ Cloud (TLS puerto 8883)

// Sensores
DHT22 → Temperatura + Humedad ambiente
Potenciómetro → Simula humedad suelo (ADC)

// Actuadores
LED Verde → Válvula abierta
LED Rojo → Válvula cerrada

// Loop principal
Cada 5 segundos:
  1. Leer sensores
  2. Crear JSON
  3. Publicar en MQTT
  4. Mostrar en Serial Monitor
```

### 10.3 Funciones Node-RED (Resumen)

```javascript
// Preparar datos para InfluxDB
msg.payload = {
    humedad_suelo: parseFloat(datos.humedad_suelo),
    temperatura: parseFloat(datos.temperatura),
    humedad_ambiente: parseFloat(datos.humedad_ambiente),
    valvula: datos.valvula === "ON" ? 1 : 0
};
msg.measurement = "sensores_pastizal";
```

---

## 11. Próximos Pasos

### 11.1 Completar para Entrega

| Tarea | Estado | Prioridad |
|-------|--------|-----------|
| Wokwi funcionando | ✅ Completo | - |
| HiveMQ configurado | ✅ Completo | - |
| Node-RED con flujo | ✅ Completo | - |
| InfluxDB guardando datos | ✅ Completo | - |
| Grafana dashboard | ⏳ En progreso | Alta |
| Modelo ML real (Python) | ⏳ Pendiente | Alta |
| Documentación (informe) | ⏳ Pendiente | Alta |

### 11.2 Modelo ML (Plan Detallado)

```
DÍA 1 (Jueves):
├── Descargar datos históricos Open-Meteo (Paute, 2020-2024)
├── Generar etiquetas con criterios agronómicos
├── Entrenar modelo (Random Forest)
└── Evaluar métricas

DÍA 2 (Viernes):
├── Crear API Flask
├── Conectar Node-RED → API Flask
├── Probar predicciones en tiempo real
└── Ajustar dashboard Grafana

DÍA 3 (Sábado):
├── Escribir informe (10-15 páginas)
├── Capturas de pantalla
├── Pruebas finales
└── Entrega
```

### 11.3 Mejoras Futuras (Post-Entrega)

- [ ] Implementar en hardware real (ESP32 físico)
- [ ] Agregar más sensores (luz solar, viento)
- [ ] Modelo LSTM para predicción temporal
- [ ] App móvil para monitoreo
- [ ] Alertas por WhatsApp/Telegram
- [ ] Modo offline con almacenamiento local

---

## 📚 Referencias

1. HiveMQ Cloud Documentation: https://docs.hivemq.com/
2. Node-RED Documentation: https://nodered.org/docs/
3. InfluxDB Cloud Documentation: https://docs.influxdata.com/
4. Open-Meteo API: https://open-meteo.com/
5. Grafana Documentation: https://grafana.com/docs/
6. Wokwi Documentation: https://docs.wokwi.com/
7. PubSubClient Library: https://pubsubclient.knolleary.net/

---

**Última actualización:** Enero 2026  
**Versión:** 1.0