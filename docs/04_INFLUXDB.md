# 04 - Configuracion de InfluxDB Cloud

## Que es InfluxDB?

InfluxDB es una **base de datos de series temporales** optimizada para datos IoT y metricas. Almacena datos con timestamps automaticos y permite consultas eficientes por rangos de tiempo.

**Caracteristicas:**
- Optimizada para datos con timestamps
- Compresion eficiente
- Lenguaje de consulta Flux
- Plan gratuito generoso

**URL:** https://cloud2.influxdata.com

---

## Rol en el Sistema

```
    FUENTES DE DATOS                    INFLUXDB                      CONSUMIDORES
    ================                    ========                      ============

    +---------------+                                                 +---------------+
    |   Node-RED    |                                                 |    Grafana    |
    |   (sensores)  |----+                                       +----|   (dashboards)|
    +---------------+    |                                       |    +---------------+
                         |         +------------------+          |
    +---------------+    |         |                  |          |
    |   Node-RED    |----+-------->|   InfluxDB       |----------+
    |   (clima)     |    |         |   Cloud          |          |
    +---------------+    |         |                  |          |    +---------------+
                         |         |  Buckets:        |          |    |   Modelo ML   |
    +---------------+    |         |  - riego_iot     |          +----|   (consultas) |
    |   Node-RED    |----+         |                  |               +---------------+
    |  (decisiones) |              |  Measurements:   |
    +---------------+              |  - sensores_     |
                                   |    pastizal      |
                                   |  - clima_        |
                                   |    openmeteo     |
                                   |  - decisiones_   |
                                   |    riego         |
                                   +------------------+
```

---

## Paso a Paso

### Paso 1: Crear Cuenta

1. Ir a https://cloud2.influxdata.com/signup
2. Seleccionar **"Get Started for Free"**
3. Registrarse con email o Google/GitHub
4. Seleccionar region: **AWS - US East (Virginia)** o la mas cercana
5. Completar el wizard inicial

---

### Paso 2: Crear Bucket

Un "bucket" es donde se almacenan los datos (como una base de datos).

1. En el menu izquierdo, click en **"Load Data"** -> **"Buckets"**
2. Click en **"Create Bucket"**
3. Configurar:
   - **Name:** `riego_iot`
   - **Delete Data:** `30 days` (o "Never" para conservar todo)
4. Click en **"Create"**

---

### Paso 3: Generar API Token

1. En el menu izquierdo, click en **"Load Data"** -> **"API Tokens"**
2. Click en **"Generate API Token"**
3. Seleccionar **"All Access API Token"**
4. Nombre: `node-red-token`
5. Click en **"Save"**

**IMPORTANTE:** Copiar el token inmediatamente. Solo se muestra una vez.

```
Ejemplo de token:
xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxX==
```

---

### Paso 4: Obtener Organization ID

1. Click en tu perfil (esquina superior derecha)
2. Click en **"About"**
3. Copiar el **Organization ID** (string alfanumerico)

```
Ejemplo:
e94345dd9c8f95c7
```

---

### Paso 5: Anotar Informacion de Conexion

Guardar estos datos para configurar Node-RED y Grafana:

| Parametro | Valor |
|-----------|-------|
| **URL** | `https://us-east-1-1.aws.cloud2.influxdata.com` |
| **Organization** | `e94345dd9c8f95c7` (tu ID) |
| **Bucket** | `riego_iot` |
| **Token** | `xXxXxX...` (tu token) |

---

## Estructura de Datos

### Measurement: sensores_pastizal

Datos de los sensores ESP32.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| time | timestamp | Automatico |
| humedad_suelo | float | 0-100% |
| temperatura | float | Grados Celsius |
| humedad_ambiente | float | 0-100% |
| valvula | integer | 0=cerrada, 1=abierta |
| **Tags:** | | |
| ubicacion | string | "paute" |
| dispositivo | string | "esp32_01" |

### Measurement: clima_openmeteo

Datos de la API climatica.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| time | timestamp | Automatico |
| temp_actual | float | Temperatura actual |
| humedad_actual | float | Humedad actual |
| prob_lluvia_24h | float | Max prob. lluvia 24h |
| precipitacion | float | Precipitacion actual (mm) |
| **Tags:** | | |
| ubicacion | string | "paute" |
| fuente | string | "open-meteo" |

### Measurement: decisiones_riego

Decisiones del modelo ML.

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| time | timestamp | Automatico |
| decision | integer | 0=no_regar, 1=regar |
| confianza | float | Nivel de confianza (%) |
| humedad_suelo | float | Valor usado para decidir |
| temperatura | float | Valor usado para decidir |
| prob_lluvia | float | Valor usado para decidir |
| **Tags:** | | |
| ubicacion | string | "paute" |

---

## Consultas Flux Utiles

### Ver ultimos datos de sensores

```flux
from(bucket: "riego_iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "sensores_pastizal")
  |> last()
```

### Promedio de humedad por hora

```flux
from(bucket: "riego_iot")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "sensores_pastizal")
  |> filter(fn: (r) => r._field == "humedad_suelo")
  |> aggregateWindow(every: 1h, fn: mean)
```

### Contar decisiones de riego

```flux
from(bucket: "riego_iot")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "decisiones_riego")
  |> filter(fn: (r) => r._field == "decision")
  |> group(columns: ["_value"])
  |> count()
```

### Ultimos datos de clima

```flux
from(bucket: "riego_iot")
  |> range(start: -3h)
  |> filter(fn: (r) => r._measurement == "clima_openmeteo")
  |> last()
```

---

## Verificacion

### Explorar Datos

1. En InfluxDB Cloud, ir a **"Data Explorer"**
2. Seleccionar bucket: `riego_iot`
3. Seleccionar measurement: `sensores_pastizal`
4. Click en **"Submit"**
5. Deberias ver graficos con los datos

### Verificar desde Node-RED

Despues de configurar Node-RED:
1. Los nodos InfluxDB deberian mostrar punto verde
2. En Data Explorer de InfluxDB deberian aparecer datos nuevos

---

## Troubleshooting

| Problema | Causa | Solucion |
|---------|-------|----------|
| Token invalido | Token incorrecto o expirado | Generar nuevo token |
| Bucket not found | Nombre incorrecto | Verificar nombre exacto |
| No aparecen datos | Node-RED no conectado | Verificar configuracion |
| Datos viejos | Retencion configurada | Verificar politica de bucket |

---

## Limites del Plan Gratuito

| Caracteristica | Limite |
|----------------|--------|
| Escrituras | 5 MB / 5 minutos |
| Consultas | 300 MB / 5 minutos |
| Almacenamiento | 2 buckets |
| Retencion | 30 dias maximo |
| Dashboards | 5 |

Para este proyecto academico, el plan gratuito es **mas que suficiente**.

---

## Siguiente Paso

Continuar con `05_GRAFANA.md` para configurar los dashboards de visualizacion.
