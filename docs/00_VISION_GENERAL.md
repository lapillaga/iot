# 00 - Vision General del Sistema

## Sistema IoT Inteligente para Riego de Pastizales Ganaderos

**Trabajo Fin de Materia** - IA Aplicada a la Industria 4.0  
**Universidad:** UTPL - Maestria en Inteligencia Artificial Aplicada  
**Autor:** Luis  
**Fecha:** Enero 2026

---

## 1. El Problema

En zonas rurales de la sierra ecuatoriana (Paute, Azuay), los pastizales para ganaderia sufren de:

- Sequias estacionales que vuelven los pastos amarillos
- Falta de sistemas de riego automatizado
- Desperdicio de agua por riego manual sin criterio tecnico
- Perdida economica por pastos de baja calidad

---

## 2. La Solucion

Un sistema IoT que:
1. **Monitorea** condiciones del suelo y ambiente en tiempo real
2. **Consulta** pronostico climatico (probabilidad de lluvia)
3. **Decide** automaticamente si regar o no usando Machine Learning
4. **Actua** abriendo/cerrando la valvula de riego
5. **Visualiza** todo en dashboards

---

## 3. Diagrama de Flujo del Sistema

```
                                    SISTEMA DE RIEGO IoT INTELIGENTE
    ================================================================================================

    CAPA FISICA (Sensores)                 CAPA COMUNICACION                    CAPA PROCESAMIENTO
    ----------------------                 -------------------                  -------------------

    +------------------+                   +------------------+                  +------------------+
    |                  |                   |                  |                  |                  |
    |  ESP32 + Wokwi   |      MQTT/TLS     |   HiveMQ Cloud   |      MQTT/TLS    |    Node-RED      |
    |                  | ----------------> |                  | ---------------> |                  |
    |  - DHT22 (temp)  |    Puerto 8883    |   Broker MQTT    |                  |  - Recibe datos  |
    |  - Pot (humedad) |                   |   en la nube     |                  |  - Procesa       |
    |  - LEDs (valvula)|                   |                  |                  |  - Decide        |
    |                  |                   |                  |                  |                  |
    +--------+---------+                   +------------------+                  +--------+---------+
             ^                                                                            |
             |                                                                            |
             |  Control valvula                                                           |
             |  (REGAR/NO_REGAR)                                                          |
             |                                                                            |
             +-------------------------------------- MQTT ---------------------------------+
                                                                                          |
                                                                                          |
    CAPA DATOS EXTERNOS                    CAPA ALMACENAMIENTO                  CAPA INTELIGENCIA
    -------------------                    --------------------                  ------------------

    +------------------+                   +------------------+                  +------------------+
    |                  |                   |                  |                  |                  |
    |   Open-Meteo     |      HTTP/REST    |   InfluxDB       |                  |   Modelo ML      |
    |   API Clima      | <---------------- |   Cloud          | <--------------- |   (Python)       |
    |                  |                   |                  |                  |                  |
    |  - Temperatura   |                   |  - sensores_     |                  |  - Random Forest |
    |  - Prob. lluvia  |                   |    pastizal      |                  |  - Prediccion    |
    |  - Pronostico    |                   |  - clima_        |                  |  - API Flask     |
    |                  |                   |    openmeteo     |                  |                  |
    |                  |                   |  - decisiones_   |                  |                  |
    |                  |                   |    riego         |                  |                  |
    |                  |                   |                  |                  |                  |
    +------------------+                   +--------+---------+                  +------------------+
                                                    |
                                                    |
                                                    v
                                           +------------------+
                                           |                  |
                                           |     Grafana      |
                                           |     Cloud        |
                                           |                  |
                                           |  - Dashboards    |
                                           |  - Alertas       |
                                           |  - Historicos    |
                                           |                  |
                                           +------------------+


    ================================================================================================
                                         FLUJO DE DATOS
    ================================================================================================


         [1]                    [2]                    [3]                    [4]
    +-----------+          +-----------+          +-----------+          +-----------+
    |  Sensores |  ------> |   MQTT    |  ------> |  Node-RED |  ------> |   Modelo  |
    |  leen     |   JSON   |  publica  |   JSON   |  procesa  |   HTTP   |    ML     |
    |  datos    |          |  topic    |          |  guarda   |          |  predice  |
    +-----------+          +-----------+          +-----------+          +-----------+
                                                        |                      |
                                                        v                      |
                                                  +-----------+                |
                                                  | InfluxDB  |                |
                                                  |  guarda   |                |
                                                  +-----------+                |
                                                        |                      |
                                                        v                      v
         [7]                    [6]                    [5]
    +-----------+          +-----------+          +-----------+
    |  Valvula  |  <------ |   MQTT    |  <------ |  Decision |
    |  actua    |  REGAR/  |  publica  |          |  REGAR o  |
    |  (LEDs)   |  NO_REGAR|  comando  |          |  NO_REGAR |
    +-----------+          +-----------+          +-----------+


    ================================================================================================
                                    TECNOLOGIAS UTILIZADAS
    ================================================================================================

    +-------------+------------------+--------------------------------+------------+
    | Capa        | Tecnologia       | Funcion                        | Costo      |
    +-------------+------------------+--------------------------------+------------+
    | Simulacion  | Wokwi            | Simular ESP32 + sensores       | Gratis     |
    | Comunic.    | HiveMQ Cloud     | Broker MQTT con TLS            | Gratis     |
    | Procesam.   | Node-RED         | Orquestacion y logica          | Gratis     |
    | Clima       | Open-Meteo API   | Pronostico del tiempo          | Gratis     |
    | Base Datos  | InfluxDB Cloud   | Almacenamiento series tiempo   | Gratis     |
    | Visual.     | Grafana Cloud    | Dashboards tiempo real         | Gratis     |
    | ML          | Python + sklearn | Modelo predictivo              | Gratis     |
    +-------------+------------------+--------------------------------+------------+

```

---

## 4. Orden de Configuracion

Para poner el sistema en funcionamiento, seguir este orden:

| Paso | Documento | Descripcion |
|------|-----------|-------------|
| 1 | `01_WOKWI.md` | Configurar simulador ESP32 con sensores |
| 2 | `02_HIVEMQ.md` | Crear broker MQTT en la nube |
| 3 | `03_NODERED.md` | Instalar y configurar Node-RED local |
| 4 | `04_INFLUXDB.md` | Crear base de datos en la nube |
| 5 | `05_GRAFANA.md` | Crear dashboards de visualizacion |
| 6 | `06_MODELO_ML.md` | Entrenar e integrar modelo de ML |
| 7 | `07_PRUEBAS.md` | Verificar funcionamiento end-to-end |

---

## 5. Flujo de Mensajes MQTT

```
TOPICS MQTT:
============

ESP32 ---> HiveMQ ---> Node-RED
           pastizal/sensores
           {
             "humedad_suelo": 45.2,
             "temperatura": 23.5,
             "humedad_ambiente": 68.0,
             "valvula": "OFF",
             "timestamp": 12345
           }

Node-RED ---> HiveMQ ---> ESP32
              pastizal/prediccion
              "REGAR" o "NO_REGAR"

Node-RED ---> HiveMQ ---> ESP32
              pastizal/valvula/control
              "ON" o "OFF" (control manual)

ESP32 ---> HiveMQ ---> Node-RED
           pastizal/valvula/estado
           "ON" o "OFF"
```

---

## 6. Variables del Sistema

### Entradas (Features para ML)

| Variable | Fuente | Rango | Descripcion |
|----------|--------|-------|-------------|
| humedad_suelo | Sensor local | 0-100% | Humedad del suelo |
| temperatura | Sensor local | 0-50 C | Temperatura ambiente |
| humedad_ambiente | Sensor local | 0-100% | Humedad del aire |
| prob_lluvia_24h | Open-Meteo | 0-100% | Probabilidad lluvia |
| hora_del_dia | Sistema | 0-23 | Hora actual |
| mes | Sistema | 1-12 | Mes actual |

### Salida (Target)

| Valor | Significado |
|-------|-------------|
| 0 | NO_REGAR |
| 1 | REGAR |

---

## 7. Proximos Pasos

Continuar con el documento `01_WOKWI.md` para configurar el simulador de hardware.
