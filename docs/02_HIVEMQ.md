# 02 - Configuracion de HiveMQ Cloud (Broker MQTT)

## Que es HiveMQ Cloud?

HiveMQ Cloud es un **broker MQTT gestionado** en la nube. Permite la comunicacion entre dispositivos IoT usando el protocolo MQTT (publish/subscribe).

**Caracteristicas:**
- Plan gratuito disponible (Serverless Free)
- Conexion segura con TLS (puerto 8883)
- Sin necesidad de mantener servidor propio

**URL:** https://www.hivemq.com/cloud/

---

## Diagrama de Comunicacion

```
    +----------------+                      +----------------+
    |                |                      |                |
    |    ESP32       |                      |   Node-RED     |
    |   (Wokwi)      |                      |   (Local)      |
    |                |                      |                |
    +-------+--------+                      +--------+-------+
            |                                        |
            |  MQTT Publish                          |  MQTT Subscribe
            |  pastizal/sensores                     |  pastizal/sensores
            |                                        |
            |          +------------------+          |
            |          |                  |          |
            +--------->|   HiveMQ Cloud   |<---------+
                       |                  |
            +----------|   Broker MQTT    |----------+
            |          |                  |          |
            |          +------------------+          |
            |                                        |
            |  MQTT Subscribe                        |  MQTT Publish
            |  pastizal/prediccion                   |  pastizal/prediccion
            v                                        v
    +-------+--------+                      +--------+-------+
    |                |                      |                |
    |    ESP32       |                      |   Node-RED     |
    |   (Recibe)     |                      |   (Envia)      |
    |                |                      |                |
    +----------------+                      +----------------+


    PUERTOS:
    ========
    - 8883: MQTT sobre TLS (usado en este proyecto)
    - 8884: WebSocket sobre TLS
    - 1883: MQTT sin cifrar (NO RECOMENDADO)
```

---

## Paso a Paso

### Paso 1: Crear Cuenta

1. Ir a https://www.hivemq.com/cloud/
2. Click en **"Try out for free"**
3. Registrarse con email o cuenta de Google/GitHub
4. Confirmar email si es necesario

---

### Paso 2: Crear Cluster

1. En el dashboard, click en **"Create Cluster"**
2. Seleccionar **"Serverless (Free)"**
3. Elegir region: **EU (Ireland)** o la mas cercana
4. Click en **"Create Cluster"**
5. Esperar ~30 segundos a que se cree

---

### Paso 3: Obtener URL del Cluster

Una vez creado, veras algo como:

```
Cluster URL: abc123def456.s1.eu.hivemq.cloud
Port (TLS): 8883
```

**ANOTAR ESTA URL** - La necesitaras para ESP32 y Node-RED.

---

### Paso 4: Crear Credenciales

1. En el cluster, ir a la pestana **"Access Management"**
2. Click en **"Add Credentials"**
3. Completar:
   - **Username:** `admin` (o el que prefieras)
   - **Password:** `TuPasswordSeguro123!`
4. Click en **"Save"**

**IMPORTANTE:** Guardar estas credenciales, las necesitaras en:
- `wokwi/sketch.ino` (lineas 25-28)
- Node-RED (configuracion del broker MQTT)

---

### Paso 5: Probar Conexion (Opcional)

HiveMQ ofrece un cliente web para probar:

1. Ir a la pestana **"Web Client"** del cluster
2. Click en **"Connect"**
3. Suscribirse al topic: `pastizal/#`
4. Cuando ejecutes Wokwi, deberias ver los mensajes llegando

---

## Configuracion en el Proyecto

### En Wokwi (sketch.ino)

Editar las lineas 25-28:

```cpp
const char* mqtt_server = "TU_CLUSTER.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "admin";
const char* mqtt_password = "TuPasswordSeguro123!";
```

### En Node-RED (flujo_riego.json)

El archivo ya tiene la estructura, pero deberas configurar manualmente:

1. Abrir Node-RED
2. Doble click en cualquier nodo MQTT
3. Click en el lapiz para editar el broker
4. En **"Security"**: agregar usuario y password

---

## Topics MQTT del Proyecto

| Topic | Direccion | Contenido |
|-------|-----------|-----------|
| `pastizal/sensores` | ESP32 -> Node-RED | JSON con datos de sensores |
| `pastizal/valvula/estado` | ESP32 -> Node-RED | "ON" o "OFF" |
| `pastizal/valvula/control` | Node-RED -> ESP32 | "ON" o "OFF" (manual) |
| `pastizal/prediccion` | Node-RED -> ESP32 | "REGAR" o "NO_REGAR" |

---

## Estructura del Mensaje JSON

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

## Verificacion

Para verificar que HiveMQ esta funcionando:

1. Abrir el **Web Client** de HiveMQ
2. Conectar con tus credenciales
3. Suscribirse a `pastizal/#`
4. Ejecutar Wokwi
5. Deberias ver mensajes cada 3 segundos:

```
Topic: pastizal/sensores
Message: {"humedad_suelo":50,"temperatura":25,...}
```

---

## Troubleshooting

| Error | Causa | Solucion |
|-------|-------|----------|
| Connection refused | Credenciales incorrectas | Verificar usuario/password |
| Timeout | URL incorrecta | Verificar URL del cluster |
| TLS error | Puerto incorrecto | Usar puerto 8883 |
| Cluster not found | Cluster eliminado | Crear nuevo cluster |

---

## Limites del Plan Gratuito

| Caracteristica | Limite |
|----------------|--------|
| Conexiones simultaneas | 100 |
| Mensajes/mes | 10 GB de trafico |
| Retencion de mensajes | No incluida |
| Persistencia de sesion | 24 horas |

Para este proyecto academico, el plan gratuito es **mas que suficiente**.

---

## Siguiente Paso

Continuar con `03_NODERED.md` para configurar Node-RED.
