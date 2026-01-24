# Sistema IoT Inteligente para Riego de Pastizales Ganaderos

## Trabajo Fin de Materia - IA Aplicada a la Industria 4.0
**Universidad:** UTPL - Maestría en Inteligencia Artificial Aplicada  
**Autor:** Luis  
**Fecha:** Enero 2026

---

## Índice

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
11. [Resultados y Conclusiones](#11-resultados-y-conclusiones)

---

## 1. Descripción del Proyecto

### 1.1 Contexto y Problema

En zonas rurales de la sierra ecuatoriana (específicamente Jerusalén, Azuay), los pastizales para ganadería sufren de:
- **Sequías estacionales** que vuelven los pastos amarillos
- **Falta de sistemas de riego automatizado**
- **Desperdicio de agua** por riego manual sin criterio técnico
- **Pérdida económica** por pastos de baja calidad

### 1.2 Solución Propuesta

Un **Sistema IoT Inteligente** que:
1. **Monitorea** en tiempo real las condiciones del suelo y ambiente
2. **Predice** la necesidad de riego usando Machine Learning (Random Forest)
3. **Integra** datos climáticos (pronóstico de lluvia via Open-Meteo)
4. **Automatiza** la decisión de regar o no regar
5. **Visualiza** toda la información en dashboards (Grafana)

### 1.3 Diferenciadores Clave

| Sistemas Tradicionales | Este Sistema |
|------------------------|--------------|
| Reglas simples: "si humedad < 30%, regar" | ML predictivo con 7 variables |
| Solo datos locales | Integración con API climática |
| Sin histórico | Base de datos temporal (InfluxDB) |
| Sin visualización | Dashboard en tiempo real (Grafana) |

### 1.4 Objetivos

- **Reducir consumo de agua** hasta 30% evitando riegos innecesarios
- **Mejorar calidad del pasto** con riego óptimo
- **Automatizar decisiones** basadas en datos y predicciones ML
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
    │   LEDs    │                     │ Open-Meteo│ │ InfluxDB  │ │  API ML   │
    │ (Válvula) │                     │    API    │ │   Cloud   │ │  (Flask)  │
    └───────────┘                     │  (Clima)  │ │   (BD)    │ │  :5001    │
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
| **ML** | Python + scikit-learn + Flask | Modelo Random Forest + API | Gratis |

### 2.3 Protocolos Utilizados

- **MQTT** (Message Queuing Telemetry Transport): Comunicación IoT ligera
- **TLS/SSL**: Cifrado de comunicaciones (puerto 8883)
- **HTTP/REST**: API Flask y Open-Meteo
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
  "temperatura": 11.5,
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
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ MQTT In      │───▶│ Procesar     │───▶│ InfluxDB     │
│ (sensores)   │    │ datos        │    │ (guardar)    │
└──────────────┘    └──────────────┘    └──────────────┘

CLIMA (cada 30 min):
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Inject       │───▶│ HTTP Request │───▶│ InfluxDB     │
│ (cada 30min) │    │ (Open-Meteo) │    │ (guardar)    │
└──────────────┘    └──────────────┘    └──────────────┘

DECISIÓN ML (cada 1 min):
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Inject       │───▶│ Preparar API │───▶│ HTTP Request │───▶│ Procesar     │
│ (cada 1min)  │    │ (JSON)       │    │ Flask :5001  │    │ respuesta    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                                                                   ▼
                                                            ┌──────────────┐
                                                            │ MQTT Out     │
                                                            │ (a ESP32)    │
                                                            └──────────────┘
```

#### Nodos Instalados

```bash
# Instalar desde Node-RED → Manage Palette
node-red-contrib-influxdb
```

---

## 4. Flujo de Datos

### 4.1 Flujo Completo (Paso a Paso)

```
PASO 1: CAPTURA DE DATOS
────────────────────────
[Wokwi] DHT22 mide temperatura: 11.5°C
[Wokwi] DHT22 mide humedad ambiente: 80%
[Wokwi] Potenciómetro simula humedad suelo: 35%

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

PASO 6: DECISIÓN ML (API Flask)
───────────────────────────────
[Node-RED] Prepara JSON con 7 features
[Node-RED] POST a http://localhost:5001/predict
[Flask] Random Forest predice: REGAR o NO_REGAR
[Flask] Retorna decisión + confianza

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
| Envío sensores | 3 segundos | Balance entre precisión y consumo |
| Consulta clima | 30 minutos | El clima no cambia rápido |
| Decisión ML | 1 minuto | Suficiente para detectar cambios |
| Dashboard | Tiempo real | Streaming de InfluxDB |

---

## 5. Configuración Paso a Paso

### 5.1 Prerequisitos

- Navegador web moderno
- Node.js instalado (para Node-RED local)
- Python 3.11+ con `uv` (gestor de paquetes)
- Cuentas gratuitas en: HiveMQ, InfluxDB Cloud, Grafana Cloud

### 5.2 Paso 1: Configurar HiveMQ Cloud

1. Ir a https://www.hivemq.com/cloud/
2. Crear cuenta gratuita
3. Crear cluster (Serverless Free)
4. Crear credenciales:
   - Username: `admin`
   - Password: `[tu-password]`
5. Anotar URL del cluster

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

Importar flujo:
- Menu → Import → Pegar contenido de `nodered/flujo_riego.json`

### 5.4 Paso 3: Configurar InfluxDB Cloud

1. Ir a https://cloud2.influxdata.com/signup
2. Crear cuenta gratuita
3. Crear bucket: `riego_iot`
4. Generar API Token (All Access)
5. Anotar: URL, Organization ID, Token

### 5.5 Paso 4: Configurar Modelo ML (Python)

```bash
cd python/

# Descargar datos históricos (2 años de Jerusalén)
uv run python 01_descargar_datos.py

# Entrenar modelo Random Forest
uv run python 02_entrenar_modelo.py

# Iniciar API Flask (puerto 5001)
uv run python 03_api_flask.py
```

### 5.6 Paso 5: Configurar Wokwi

1. Ir a https://wokwi.com
2. Crear nuevo proyecto ESP32
3. Copiar código de `wokwi/sketch.ino`
4. Copiar diagrama de `wokwi/diagram.json`
5. Agregar librerías: PubSubClient, DHT sensor library for ESPx, ArduinoJson
6. Editar credenciales MQTT en el código

### 5.7 Paso 6: Configurar Grafana Cloud

1. Ir a https://grafana.com/products/cloud/
2. Crear cuenta gratuita
3. Agregar Data Source → InfluxDB
4. Configurar conexión con credenciales de InfluxDB
5. Crear dashboard con paneles

---

## 6. Modelo de Machine Learning

### 6.1 Descripción del Modelo

El sistema utiliza un modelo **Random Forest Classifier** entrenado con datos climáticos históricos de Jerusalén, Ecuador.

#### Datos de Entrenamiento

| Característica | Valor |
|----------------|-------|
| **Ubicación** | Jerusalén, Azuay, Ecuador |
| **Coordenadas** | -2.690425, -78.935117 |
| **Período** | 2 años (2024-2026) |
| **Registros** | 17,424 (horarios) |
| **Fuente** | Open-Meteo Historical API |

#### Distribución de Clases

| Clase | Cantidad | Porcentaje |
|-------|----------|------------|
| NO_REGAR | 15,584 | 89.4% |
| REGAR | 1,840 | 10.6% |

### 6.2 Variables de Entrada (Features)

| Variable | Fuente | Tipo | Importancia |
|----------|--------|------|-------------|
| humedad_suelo | Sensor local | float (0-100%) | **73.7%** |
| mes | Sistema | int (1-12) | **10.4%** |
| prob_lluvia | Open-Meteo | float (0-100%) | **6.5%** |
| hora | Sistema | int (0-23) | **4.3%** |
| temperatura | Sensor local | float (°C) | 1.9% |
| humedad_ambiente | Sensor local | float (0-100%) | 1.7% |
| precipitacion | Open-Meteo | float (mm) | 1.5% |

### 6.3 Métricas del Modelo

| Métrica | Valor |
|---------|-------|
| **Accuracy** | 99.83% |
| **Precision** | 98.92% |
| **Recall** | 99.46% |
| **F1-Score** | 99.19% |
| **ROC-AUC** | 1.0 |

#### Matriz de Confusión

```
                 Predicho
              NO_REGAR  REGAR
Real NO_REGAR    3113       4
Real REGAR          2     366
```

### 6.4 Parámetros del Random Forest

```python
RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1,
    "class_weight": "balanced"
}
```

### 6.5 Criterios de Etiquetado (basados en FAO)

Las etiquetas de entrenamiento se generaron usando criterios agronómicos:

| Regla | Condición | Decisión |
|-------|-----------|----------|
| 1 | Humedad suelo < 20% | REGAR (urgente) |
| 2 | Humedad suelo < 35% y prob_lluvia > 70% | NO_REGAR (esperar) |
| 3 | Humedad suelo < 40% y temp > 25°C y prob_lluvia < 40% | REGAR |
| 4 | Humedad suelo < 45% y hora entre 5-8 AM y prob_lluvia < 50% | REGAR |
| 5 | Humedad suelo >= 45% | NO_REGAR |

### 6.6 API Flask

#### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Estado del servicio |
| GET | `/features` | Features requeridas |
| POST | `/predict` | Hacer predicción |
| GET | `/model/info` | Información del modelo |

#### Ejemplo de Uso

```bash
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "humedad_suelo": 25,
    "temperatura": 12,
    "humedad_ambiente": 60,
    "precipitacion": 0,
    "prob_lluvia": 10,
    "hora": 7,
    "mes": 8
  }'
```

#### Respuesta

```json
{
  "decision": "REGAR",
  "decision_int": 1,
  "probabilidad_regar": 0.978,
  "probabilidad_no_regar": 0.022,
  "confianza": 97.8,
  "timestamp": "2026-01-23T22:23:43.059142"
}
```

---

## 7. API Climática (Open-Meteo)

### 7.1 ¿Por qué Open-Meteo?

| Característica | Open-Meteo | Otras APIs |
|----------------|------------|------------|
| **Costo** | Gratis | Pago o limitado |
| **API Key** | No requiere | Requiere |
| **Datos históricos** | Desde 1940 | Limitado |
| **Pronóstico** | Hasta 16 días | Variable |

### 7.2 Endpoint Utilizado

```
https://api.open-meteo.com/v1/forecast
  ?latitude=-2.690425
  &longitude=-78.935117
  &current=temperature_2m,relative_humidity_2m,precipitation
  &hourly=precipitation_probability
  &daily=precipitation_sum,precipitation_probability_max
  &timezone=America/Guayaquil
  &forecast_days=3
```

### 7.3 Variables Obtenidas

| Variable | Descripción | Uso |
|----------|-------------|-----|
| temperature_2m | Temperatura actual | Feature ML |
| relative_humidity_2m | Humedad actual | Feature ML |
| precipitation | Precipitación actual | Feature ML |
| precipitation_probability | Prob. lluvia por hora | Feature ML (clave) |
| precipitation_sum | Lluvia acumulada día | Histórico |

### 7.4 Coordenadas

```
Ubicación: Jerusalén, Azuay, Ecuador
Latitud:   -2.690425
Longitud:  -78.935117
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
| ubicacion (tag) | string | "jerusalen" |
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
| probabilidad_regar | float | 0-1 |
| humedad_suelo | float | % |
| temperatura | float | °C |
| prob_lluvia | float | % |
| modelo (tag) | string | "random_forest" |

---

## 9. Visualización (Grafana)

### 9.1 Dashboard Propuesto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Sistema de Riego IoT - Pastizales Jerusalén                                │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│                 │                 │                 │                       │
│  HUMEDAD SUELO  │  TEMPERATURA    │  VÁLVULA        │  PROB. LLUVIA 24H     │
│                 │                 │                 │                       │
│     ┌───┐       │     ┌───┐       │                 │      ┌───┐            │
│     │45%│       │     │11°│       │    CERRADA      │      │30%│            │
│     └───┘       │     └───┘       │                 │      └───┘            │
│    [GAUGE]      │    [GAUGE]      │    [STAT]       │     [GAUGE]           │
│                 │                 │                 │                       │
├─────────────────┴─────────────────┴─────────────────┴───────────────────────┤
│                                                                             │
│  HISTÓRICO DE SENSORES (última hora)                                        │
│  ════════════════════════════════════════════════════════════════════════   │
│  ╱╲    ╱╲                                                                   │
│ ╱  ╲  ╱  ╲  ────── Humedad suelo                                            │
│╱    ╲╱    ╲ ────── Temperatura                                              │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DECISIONES DEL MODELO ML (últimas 24h)                                     │
│  Modelo: Random Forest | Accuracy: 99.8%                                    │
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
proyecto/
├── CLAUDE.md                    # Este documento
├── wokwi/
│   ├── sketch.ino              # Código ESP32
│   ├── diagram.json            # Circuito Wokwi
│   └── libraries.txt           # Dependencias
├── nodered/
│   └── flujo_riego.json        # Flujo importable (con integración Flask)
├── python/
│   ├── 01_descargar_datos.py   # Descarga datos Open-Meteo históricos
│   ├── 02_entrenar_modelo.py   # Entrena Random Forest
│   ├── 03_api_flask.py         # API REST para predicciones
│   ├── pyproject.toml          # Dependencias Python (uv)
│   ├── dataset/
│   │   ├── datos_historicos_jerusalen.csv
│   │   └── parametros_riego.txt
│   └── models/
│       ├── modelo_riego.joblib # Modelo entrenado
│       └── metricas.txt        # Métricas de evaluación
└── docs/
    ├── 00_VISION_GENERAL.md
    ├── 01_WOKWI.md
    ├── 02_HIVEMQ.md
    ├── 03_NODERED.md
    ├── 04_INFLUXDB.md
    ├── 05_GRAFANA.md
    ├── 06_MODELO_ML.md
    └── 07_PRUEBAS.md
```

### 10.2 Ejecución del Sistema

```bash
# 1. Iniciar API Flask (terminal 1)
cd python/
uv run python 03_api_flask.py

# 2. Iniciar Node-RED (terminal 2)
node-red
# Abrir http://localhost:1880 e importar flujo

# 3. Abrir Wokwi (navegador)
# https://wokwi.com - cargar proyecto

# 4. Ver Grafana (navegador)
# https://[tu-instancia].grafana.net
```

---

## 11. Resultados y Conclusiones

### 11.1 Resultados Obtenidos

| Componente | Estado | Observaciones |
|------------|--------|---------------|
| Wokwi (ESP32) | ✅ Funcionando | Simulación completa |
| HiveMQ (MQTT) | ✅ Funcionando | Comunicación TLS |
| Node-RED | ✅ Funcionando | Integrado con API Flask |
| InfluxDB | ✅ Funcionando | Almacenando datos |
| Modelo ML | ✅ Funcionando | 99.8% accuracy |
| API Flask | ✅ Funcionando | Puerto 5001 |
| Grafana | ⏳ Pendiente | Dashboard por crear |

### 11.2 Pruebas del Modelo

| Escenario | Humedad | Condiciones | Decisión | Confianza |
|-----------|---------|-------------|----------|-----------|
| Suelo crítico | 15% | Sin lluvia | REGAR | 97.8% |
| Suelo seco | 30% | Calor, sin lluvia | REGAR | 57.3% |
| Seco + lluvia próxima | 32% | Prob lluvia 85% | NO_REGAR | 94.8% |
| Suelo húmedo | 65% | Normal | NO_REGAR | 99.4% |
| Lloviendo | 55% | Precipitación activa | NO_REGAR | 100% |
| Post-lluvia | 75% | Recién llovió | NO_REGAR | 100% |

### 11.3 Conclusiones

1. **El modelo ML supera las reglas hardcodeadas**: Con 99.8% de accuracy, el Random Forest aprende patrones complejos que serían difíciles de programar manualmente.

2. **La variable más importante es la humedad del suelo** (73.7%), seguida del mes (estacionalidad) y la probabilidad de lluvia.

3. **La integración IoT + ML es viable**: El sistema demuestra que es posible combinar sensores, cloud, y machine learning en un flujo coherente.

4. **El ahorro de agua es significativo**: Al no regar cuando va a llover (escenario 3), el sistema evita riegos innecesarios.

### 11.4 Mejoras Futuras

- [ ] Implementar en hardware real (ESP32 físico)
- [ ] Agregar más sensores (luz solar, viento)
- [ ] Modelo LSTM para predicción temporal
- [ ] App móvil para monitoreo
- [ ] Alertas por WhatsApp/Telegram
- [ ] Modo offline con almacenamiento local

---

## Referencias

1. HiveMQ Cloud Documentation: https://docs.hivemq.com/
2. Node-RED Documentation: https://nodered.org/docs/
3. InfluxDB Cloud Documentation: https://docs.influxdata.com/
4. Open-Meteo API: https://open-meteo.com/
5. Grafana Documentation: https://grafana.com/docs/
6. Wokwi Documentation: https://docs.wokwi.com/
7. scikit-learn Random Forest: https://scikit-learn.org/stable/modules/ensemble.html#random-forests
8. FAO Irrigation and Drainage Paper 56: https://www.fao.org/3/x0490e/x0490e00.htm

---

**Última actualización:** Enero 2026  
**Versión:** 2.0
