# 03 - Configuracion de Node-RED

## Que es Node-RED?

Node-RED es una herramienta de **programacion visual basada en flujos**, ideal para IoT. Permite conectar dispositivos, APIs y servicios arrastrando y conectando nodos.

**Caracteristicas:**
- Interfaz visual drag-and-drop
- Gran ecosistema de nodos
- Perfecto para prototipado rapido
- Corre localmente en tu maquina

---

## Rol en el Sistema

```
                                    NODE-RED
    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │   +-----------+     +-----------+     +-----------+              │
    │   |           |     |           |     |           |              │
    │   |  MQTT In  |---->| Procesar  |---->| InfluxDB  |              │
    │   | (sensores)|     |   datos   |     |  (guardar)|              │
    │   |           |     |           |     |           |              │
    │   +-----------+     +-----------+     +-----------+              │
    │                                                                  │
    │   +-----------+     +-----------+     +-----------+              │
    │   |           |     |           |     |           |              │
    │   |   HTTP    |---->| Procesar  |---->| InfluxDB  |              │
    │   |(Open-Meteo|     |   clima   |     |  (guardar)|              │
    │   |           |     |           |     |           |              │
    │   +-----------+     +-----------+     +-----------+              │
    │                                                                  │
    │   +-----------+     +-----------+     +-----------+              │
    │   |           |     |           |     |           |              │
    │   |  Inject   |---->| Modelo ML |---->| MQTT Out  |              │
    │   | (cada 1m) |     | (decision)|     | (a ESP32) |              │
    │   |           |     |           |     |           |              │
    │   +-----------+     +-----------+     +-----------+              │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
            ^                                        |
            |                                        |
            | MQTT                                   | MQTT
            | (datos sensores)                       | (REGAR/NO_REGAR)
            |                                        v
    +---------------+                        +---------------+
    |    HiveMQ     |                        |     ESP32     |
    |    Cloud      |                        |    (Wokwi)    |
    +---------------+                        +---------------+
```

---

## Paso a Paso

### Paso 1: Instalar Node.js

Node-RED requiere Node.js. Si no lo tienes:

**macOS (con Homebrew):**
```bash
brew install node
```

**Verificar instalacion:**
```bash
node --version   # Deberia mostrar v18.x o superior
npm --version    # Deberia mostrar 9.x o superior
```

---

### Paso 2: Instalar Node-RED

```bash
npm install -g --unsafe-perm node-red
```

---

### Paso 3: Ejecutar Node-RED

```bash
node-red
```

Veras algo como:
```
Welcome to Node-RED
===================

4 Jan 12:00:00 - [info] Node-RED version: v3.1.0
4 Jan 12:00:00 - [info] Node.js  version: v18.17.0
4 Jan 12:00:00 - [info] Server now running at http://127.0.0.1:1880/
```

**Abrir en navegador:** http://localhost:1880

---

### Paso 4: Instalar Nodos Adicionales

En Node-RED:

1. Click en menu (tres lineas horizontales, esquina superior derecha)
2. Click en **"Manage palette"**
3. Ir a pestana **"Install"**
4. Buscar e instalar:
   - `node-red-contrib-influxdb`

---

### Paso 5: Importar Flujo del Proyecto

1. Click en menu -> **"Import"**
2. Click en **"select a file to import"**
3. Seleccionar: `nodered/flujo_riego.json`
4. Click en **"Import"**

El flujo aparecera en el canvas.

---

## Configuracion Manual Requerida

**IMPORTANTE:** El archivo JSON importado NO incluye credenciales por seguridad. Debes configurar manualmente:

### Configurar Broker MQTT (HiveMQ)

1. Doble click en cualquier nodo MQTT (ej: "Sensores ESP32")
2. Click en el **lapiz** junto a "Server"
3. Verificar que la URL sea correcta: `tu-cluster.s1.eu.hivemq.cloud`
4. Ir a pestana **"Security"**
5. Completar:
   - **Username:** `admin`
   - **Password:** `TuPasswordDeHiveMQ`
6. Ir a pestana **"TLS Configuration"**
7. Marcar **"Enable secure (SSL/TLS) connection"**
8. Click en **"Update"**
9. Click en **"Done"**

### Configurar InfluxDB

1. Doble click en cualquier nodo InfluxDB (ej: "InfluxDB Cloud")
2. Click en el **lapiz** junto a "Server"
3. Verificar/completar:
   - **Version:** 2.0
   - **URL:** `https://us-east-1-1.aws.cloud2.influxdata.com`
   - **Token:** `TuTokenDeInfluxDB` (ver paso 04_INFLUXDB.md)
   - **Organization:** `TuOrganizacionID`
   - **Bucket:** `riego_iot`
4. Click en **"Update"**
5. Click en **"Done"**

---

### Paso 6: Deploy

1. Click en boton rojo **"Deploy"** (esquina superior derecha)
2. Verificar que no haya errores en los nodos

---

## Descripcion de los Nodos

### Seccion: Recepcion de Sensores

| Nodo | Tipo | Funcion |
|------|------|---------|
| Sensores ESP32 | mqtt in | Recibe datos del topic `pastizal/sensores` |
| Procesar datos | function | Extrae valores y guarda en contexto |
| Ver datos sensores | debug | Muestra datos en sidebar |

### Seccion: Guardar en InfluxDB

| Nodo | Tipo | Funcion |
|------|------|---------|
| Preparar para InfluxDB | function | Formatea datos para InfluxDB |
| InfluxDB Cloud | influxdb out | Envia datos a la base |

### Seccion: Consulta Clima

| Nodo | Tipo | Funcion |
|------|------|---------|
| Cada 30 min | inject | Dispara cada 30 minutos |
| Open-Meteo API | http request | Consulta API de clima |
| Procesar clima | function | Extrae probabilidad de lluvia |
| Clima a InfluxDB | influxdb out | Guarda datos climaticos |

### Seccion: Modelo ML

| Nodo | Tipo | Funcion |
|------|------|---------|
| Cada 1 min | inject | Dispara cada minuto |
| Modelo ML (Decision) | function | Aplica reglas/ML para decidir |
| Regar? | switch | Separa REGAR de NO_REGAR |
| Enviar a ESP32 | mqtt out | Publica decision |

### Seccion: Control Manual

| Nodo | Tipo | Funcion |
|------|------|---------|
| ABRIR Valvula | inject | Envia comando ON |
| CERRAR Valvula | inject | Envia comando OFF |
| Control valvula | mqtt out | Publica en topic de control |

---

## Verificacion

### Ver Debug

1. Click en icono de **bug** (Debug) en sidebar derecha
2. Deberias ver mensajes cuando lleguen datos de Wokwi

### Estados de los Nodos

- **Punto verde:** Conectado/funcionando
- **Punto amarillo:** Esperando conexion
- **Punto rojo:** Error
- **Anillo:** Sin conexion

---

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| MQTT desconectado | Verificar credenciales y URL de HiveMQ |
| InfluxDB error | Verificar token y bucket |
| No llegan datos | Verificar que Wokwi este publicando |
| Nodo en rojo | Leer mensaje de error, usualmente credenciales |

---

## Comandos Utiles

```bash
# Iniciar Node-RED
node-red

# Iniciar en background
node-red &

# Ver logs
node-red-log

# Detener (si esta en foreground)
Ctrl + C
```

---

## Archivos de Node-RED

Ubicacion de archivos (macOS):
```
~/.node-red/
├── flows.json          # Flujos actuales
├── flows_cred.json     # Credenciales (encriptado)
├── settings.js         # Configuracion
└── package.json        # Dependencias
```

---

## Siguiente Paso

Continuar con `04_INFLUXDB.md` para configurar la base de datos.
