# 05 - Configuracion de Grafana Cloud

## Que es Grafana?

Grafana es una plataforma de **visualizacion y observabilidad**. Permite crear dashboards interactivos con graficos, gauges, alertas y mas.

**Caracteristicas:**
- Dashboards interactivos
- Multiples fuentes de datos
- Alertas configurables
- Plan gratuito disponible

**URL:** https://grafana.com/products/cloud/

---

## Rol en el Sistema

```
    +------------------+
    |    InfluxDB      |
    |    Cloud         |
    |                  |
    | - sensores_      |
    |   pastizal       |
    | - clima_openmeteo|
    | - decisiones_    |
    |   riego          |
    +--------+---------+
             |
             | Flux queries
             |
             v
    +------------------+
    |    Grafana       |
    |    Cloud         |
    |                  |
    |  +------------+  |
    |  | Dashboard  |  |
    |  |            |  |
    |  | [Gauge]    |  |
    |  | Humedad    |  |
    |  |            |  |
    |  | [Graph]    |  |
    |  | Historico  |  |
    |  |            |  |
    |  | [Stat]     |  |
    |  | Valvula    |  |
    |  +------------+  |
    |                  |
    +------------------+
             |
             | HTTP/Browser
             v
    +------------------+
    |    Usuario       |
    |    (Navegador)   |
    +------------------+
```

---

## Paso a Paso

### Paso 1: Crear Cuenta

1. Ir a https://grafana.com/products/cloud/
2. Click en **"Create free account"**
3. Registrarse con email o Google/GitHub
4. Seleccionar plan: **Free** (hasta 10k metricas)
5. Elegir nombre para tu instancia (ej: `luis-utpl`)

Tu URL sera algo como: `https://luis-utpl.grafana.net`

---

### Paso 2: Agregar Data Source (InfluxDB)

1. En el menu izquierdo, ir a **Connections** -> **Data Sources**
2. Click en **"Add data source"**
3. Buscar y seleccionar **"InfluxDB"**

Configurar:

| Campo | Valor |
|-------|-------|
| **Name** | InfluxDB Cloud |
| **Query Language** | Flux |
| **URL** | `https://us-east-1-1.aws.cloud2.influxdata.com` |
| **Auth - Basic auth** | OFF |
| **InfluxDB Details:** | |
| Organization | `tu-organization-id` |
| Token | `tu-api-token` |
| Default Bucket | `riego_iot` |

4. Click en **"Save & Test"**
5. Deberia mostrar: "datasource is working"

---

### Paso 3: Crear Dashboard

1. En menu izquierdo, click en **"Dashboards"**
2. Click en **"New"** -> **"New Dashboard"**
3. Click en **"Add visualization"**

---

### Paso 4: Crear Paneles

#### Panel 1: Gauge - Humedad del Suelo

**Query (Flux):**
```flux
from(bucket: "riego_iot")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "sensores_pastizal")
  |> filter(fn: (r) => r._field == "humedad_suelo")
  |> last()
```

**Configuracion:**
- **Visualization:** Gauge
- **Title:** Humedad del Suelo
- **Unit:** Percent (0-100)
- **Min:** 0, **Max:** 100
- **Thresholds:**
  - 0-30: Rojo (seco)
  - 30-60: Amarillo (ok)
  - 60-100: Verde (humedo)

---

#### Panel 2: Gauge - Temperatura

**Query (Flux):**
```flux
from(bucket: "riego_iot")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "sensores_pastizal")
  |> filter(fn: (r) => r._field == "temperatura")
  |> last()
```

**Configuracion:**
- **Visualization:** Gauge
- **Title:** Temperatura
- **Unit:** Celsius
- **Min:** 0, **Max:** 50
- **Thresholds:**
  - 0-15: Azul (frio)
  - 15-30: Verde (normal)
  - 30-50: Rojo (caliente)

---

#### Panel 3: Stat - Estado Valvula

**Query (Flux):**
```flux
from(bucket: "riego_iot")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "sensores_pastizal")
  |> filter(fn: (r) => r._field == "valvula")
  |> last()
```

**Configuracion:**
- **Visualization:** Stat
- **Title:** Estado Valvula
- **Value mappings:**
  - 0 -> "CERRADA" (rojo)
  - 1 -> "ABIERTA" (verde)

---

#### Panel 4: Gauge - Probabilidad de Lluvia

**Query (Flux):**
```flux
from(bucket: "riego_iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "clima_openmeteo")
  |> filter(fn: (r) => r._field == "prob_lluvia_24h")
  |> last()
```

**Configuracion:**
- **Visualization:** Gauge
- **Title:** Prob. Lluvia 24h
- **Unit:** Percent (0-100)
- **Thresholds:**
  - 0-30: Verde (sin lluvia)
  - 30-70: Amarillo (posible)
  - 70-100: Azul (lluvia probable)

---

#### Panel 5: Time Series - Historico de Sensores

**Query (Flux):**
```flux
from(bucket: "riego_iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "sensores_pastizal")
  |> filter(fn: (r) => r._field == "humedad_suelo" or r._field == "temperatura" or r._field == "humedad_ambiente")
```

**Configuracion:**
- **Visualization:** Time series
- **Title:** Historico de Sensores
- **Legend:** Mostrar

---

#### Panel 6: Bar Gauge - Decisiones ML

**Query (Flux):**
```flux
from(bucket: "riego_iot")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "decisiones_riego")
  |> filter(fn: (r) => r._field == "decision")
  |> group()
  |> count()
```

**Configuracion:**
- **Visualization:** Bar gauge
- **Title:** Decisiones ML (24h)

---

### Paso 5: Organizar Dashboard

Arrastra y redimensiona los paneles para crear un layout como:

```
+------------------+------------------+------------------+------------------+
|                  |                  |                  |                  |
|  HUMEDAD SUELO   |   TEMPERATURA    |    VALVULA       |  PROB. LLUVIA    |
|     [GAUGE]      |     [GAUGE]      |     [STAT]       |    [GAUGE]       |
|                  |                  |                  |                  |
+------------------+------------------+------------------+------------------+
|                                                                           |
|                    HISTORICO DE SENSORES (ultima hora)                    |
|                           [TIME SERIES]                                   |
|                                                                           |
+---------------------------------------------------------------------------+
|                                                                           |
|                    DECISIONES DEL MODELO ML (24h)                         |
|                           [BAR GAUGE]                                     |
|                                                                           |
+---------------------------------------------------------------------------+
```

---

### Paso 6: Guardar Dashboard

1. Click en el icono de **disco** (Save)
2. Nombre: `Sistema de Riego IoT - Pastizales Paute`
3. Click en **"Save"**

---

## Configuracion de Auto-Refresh

1. En la esquina superior derecha, click en el dropdown de tiempo
2. Seleccionar **"Last 1 hour"**
3. Activar **Auto-refresh:** `5s` (cada 5 segundos)

---

## Alertas (Opcional)

Puedes configurar alertas para notificarte cuando:
- Humedad del suelo < 20% (critico)
- Temperatura > 35C (muy caliente)
- Sin datos por mas de 10 minutos

1. En un panel, click en **"Alert"** tab
2. Click en **"Create alert rule"**
3. Configurar condicion y notificacion

---

## Verificacion

1. Ejecutar Wokwi (enviar datos)
2. Verificar que Node-RED procesa y envia a InfluxDB
3. En Grafana, los paneles deberian actualizar en tiempo real
4. Girar potenciometro en Wokwi -> ver cambio en Gauge de humedad

---

## Troubleshooting

| Problema | Causa | Solucion |
|---------|-------|----------|
| "No data" en paneles | Query incorrecto o sin datos | Verificar query en Data Explorer |
| Error de conexion | Token/URL incorrectos | Verificar Data Source |
| Datos no actualizan | Auto-refresh desactivado | Activar auto-refresh |
| Graficos vacios | Rango de tiempo incorrecto | Cambiar a "Last 1 hour" |

---

## Limites del Plan Gratuito

| Caracteristica | Limite |
|----------------|--------|
| Usuarios | 3 |
| Dashboards | Ilimitados |
| Alertas | 100 |
| Retencion metricas | 14 dias |

---

## Siguiente Paso

Continuar con `06_MODELO_ML.md` para entrenar e integrar el modelo de Machine Learning.
