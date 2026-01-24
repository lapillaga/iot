# 07 - Pruebas End-to-End

## Objetivo

Verificar que todos los componentes del sistema funcionan correctamente de forma integrada.

---

## Checklist de Componentes

Antes de las pruebas, verificar que todo este corriendo:

| Componente | Como verificar | Estado |
|------------|----------------|--------|
| HiveMQ Cloud | Web Client conecta | [ ] |
| Node-RED | http://localhost:1880 responde | [ ] |
| InfluxDB Cloud | Data Explorer funciona | [ ] |
| Grafana Cloud | Dashboard carga | [ ] |
| API Flask (ML) | http://localhost:5000/health | [ ] |
| Wokwi | Simulacion corre | [ ] |

---

## Diagrama de Prueba

```
    PRUEBA END-TO-END
    =================

    [1] INICIAR                          [4] VERIFICAR
    +-----------+                        +-----------+
    |  Wokwi    |                        |  Grafana  |
    | (girar    |                        | (ver      |
    |  potencio)|                        |  gauges)  |
    +-----+-----+                        +-----+-----+
          |                                    ^
          | MQTT                               | Query
          v                                    |
    [2] BROKER                           +-----------+
    +-----------+                        | InfluxDB  |
    |  HiveMQ   |                        | (datos    |
    |  Cloud    |                        |  guardados)|
    +-----+-----+                        +-----+-----+
          |                                    ^
          | MQTT                               |
          v                                    |
    [3] PROCESAR                               |
    +-----------+     +----------+     +-------+
    | Node-RED  |---->| API Flask|---->| Guardar
    | (recibir) |     | (predecir)|    | datos
    +-----------+     +----------+     +-------+
          |
          | MQTT (REGAR/NO_REGAR)
          v
    [5] ACTUAR
    +-----------+
    |  Wokwi    |
    | (LED      |
    |  cambia)  |
    +-----------+
```

---

## Prueba 1: Flujo de Sensores

### Objetivo
Verificar que los datos van desde Wokwi hasta InfluxDB.

### Pasos

1. **Iniciar Wokwi**
   - Abrir proyecto en Wokwi
   - Click en Play (iniciar simulacion)
   - Verificar en Serial Monitor:
   ```
   ✅ WiFi conectado!
   ✅ MQTT Conectado!
   📊 DATOS ENVIADOS: {...}
   ```

2. **Verificar HiveMQ**
   - Abrir Web Client de HiveMQ
   - Suscribirse a `pastizal/#`
   - Deberian llegar mensajes cada 3 segundos

3. **Verificar Node-RED**
   - Abrir http://localhost:1880
   - Ver panel Debug (sidebar derecha)
   - Deberian aparecer los datos de sensores

4. **Verificar InfluxDB**
   - Abrir Data Explorer de InfluxDB
   - Query:
   ```flux
   from(bucket: "riego_iot")
     |> range(start: -5m)
     |> filter(fn: (r) => r._measurement == "sensores_pastizal")
   ```
   - Deberian aparecer datos recientes

### Resultado Esperado
- [ ] Wokwi publica cada 3 segundos
- [ ] HiveMQ recibe mensajes
- [ ] Node-RED procesa datos
- [ ] InfluxDB almacena datos

---

## Prueba 2: Consulta de Clima

### Objetivo
Verificar que Open-Meteo API funciona y los datos se guardan.

### Pasos

1. **Forzar consulta de clima**
   - En Node-RED, click en el nodo "Cada 30 min"
   - Click en el boton de inyectar (cuadrado a la izquierda)

2. **Verificar Debug**
   - En sidebar de Debug, buscar datos de clima:
   ```json
   {
     "temp_actual": 18.5,
     "humedad_actual": 72,
     "max_prob_lluvia_24h": 45,
     ...
   }
   ```

3. **Verificar InfluxDB**
   - Query:
   ```flux
   from(bucket: "riego_iot")
     |> range(start: -1h)
     |> filter(fn: (r) => r._measurement == "clima_openmeteo")
   ```

### Resultado Esperado
- [ ] API Open-Meteo responde
- [ ] Node-RED procesa clima
- [ ] InfluxDB guarda datos de clima

---

## Prueba 3: Modelo ML

### Objetivo
Verificar que el modelo ML hace predicciones correctas.

### Pasos

1. **Verificar API Flask**
   ```bash
   curl http://localhost:5000/health
   ```
   Respuesta esperada: `{"status": "ok", "model": "loaded"}`

2. **Probar prediccion - Suelo seco**
   ```bash
   curl -X POST http://localhost:5000/predict \
     -H "Content-Type: application/json" \
     -d '{
       "humedad_suelo": 20,
       "temperatura": 28,
       "humedad_ambiente": 50,
       "precipitacion": 0,
       "hora": 8,
       "mes": 6
     }'
   ```
   Respuesta esperada: `{"decision": "REGAR", ...}`

3. **Probar prediccion - Suelo humedo**
   ```bash
   curl -X POST http://localhost:5000/predict \
     -H "Content-Type: application/json" \
     -d '{
       "humedad_suelo": 70,
       "temperatura": 20,
       "humedad_ambiente": 80,
       "precipitacion": 2,
       "hora": 14,
       "mes": 6
     }'
   ```
   Respuesta esperada: `{"decision": "NO_REGAR", ...}`

4. **Forzar decision en Node-RED**
   - Click en nodo "Cada 1 min" para inyectar
   - Verificar Debug muestra decision del modelo

### Resultado Esperado
- [ ] API Flask responde correctamente
- [ ] Predicciones son logicas
- [ ] Node-RED integra con API

---

## Prueba 4: Control de Valvula

### Objetivo
Verificar que ESP32 responde a comandos.

### Pasos

1. **Enviar comando manual ON**
   - En Node-RED, click en nodo "ABRIR Valvula"
   - En Wokwi, verificar:
     - Serial Monitor: `🚿 VALVULA ABIERTA`
     - LED Verde enciende
     - LED Rojo apaga

2. **Enviar comando manual OFF**
   - En Node-RED, click en nodo "CERRAR Valvula"
   - En Wokwi, verificar:
     - Serial Monitor: `🔴 VALVULA CERRADA`
     - LED Verde apaga
     - LED Rojo enciende

3. **Probar con decision ML**
   - En Wokwi, girar potenciometro a valor bajo (simular suelo seco)
   - Esperar ~1 minuto (o forzar inyeccion)
   - Verificar que LED Verde enciende (decision REGAR)

### Resultado Esperado
- [ ] Comando ON abre valvula
- [ ] Comando OFF cierra valvula
- [ ] Decision ML automatica funciona

---

## Prueba 5: Dashboard Grafana

### Objetivo
Verificar visualizacion en tiempo real.

### Pasos

1. **Abrir dashboard**
   - Ir a tu instancia de Grafana Cloud
   - Abrir dashboard "Sistema de Riego IoT"

2. **Verificar paneles**
   - Gauge Humedad Suelo: muestra valor actual
   - Gauge Temperatura: muestra valor actual
   - Stat Valvula: muestra ABIERTA/CERRADA
   - Time Series: muestra historico

3. **Probar actualizacion en tiempo real**
   - En Wokwi, girar potenciometro
   - En Grafana, verificar que Gauge de Humedad cambia
   - (con auto-refresh de 5s)

### Resultado Esperado
- [ ] Todos los paneles muestran datos
- [ ] Actualizacion en tiempo real funciona
- [ ] Colores de umbrales correctos

---

## Prueba 6: Escenario Completo

### Objetivo
Simular un dia completo de operacion.

### Escenarios

| Escenario | Potenciometro | Esperado |
|-----------|---------------|----------|
| Suelo critico | 0-20% | REGAR (LED verde) |
| Suelo seco | 20-40% | REGAR si no llueve |
| Suelo ok | 40-60% | Depende de condiciones |
| Suelo humedo | 60-100% | NO_REGAR (LED rojo) |

### Pasos

1. Girar potenciometro a diferentes valores
2. Esperar decision del modelo (1 minuto)
3. Verificar que LED correcto enciende
4. Verificar en Grafana el historico

---

## Troubleshooting Comun

| Problema | Causa Probable | Solucion |
|----------|----------------|----------|
| Wokwi no conecta MQTT | Credenciales incorrectas | Verificar usuario/password |
| Node-RED no recibe datos | Broker MQTT mal configurado | Verificar conexion TLS |
| InfluxDB sin datos | Token incorrecto | Regenerar token |
| Grafana "No data" | Query incorrecta o bucket vacio | Verificar en Data Explorer |
| API Flask error 500 | Modelo no cargado | Verificar modelo.pkl existe |
| LEDs no cambian | Topic incorrecto | Verificar topics MQTT |

---

## Metricas de Exito

| Metrica | Objetivo | Actual |
|---------|----------|--------|
| Latencia Wokwi -> InfluxDB | < 5 segundos | |
| Precision modelo ML | > 85% | |
| Uptime sistema | > 95% | |
| Decisiones correctas | > 90% | |

---

## Capturas de Pantalla Sugeridas

Para el informe final, capturar:

1. [ ] Wokwi corriendo con Serial Monitor
2. [ ] HiveMQ Web Client recibiendo mensajes
3. [ ] Node-RED flujo completo
4. [ ] Node-RED Debug con datos
5. [ ] InfluxDB Data Explorer con graficos
6. [ ] Grafana Dashboard completo
7. [ ] Terminal con API Flask corriendo
8. [ ] curl con respuesta de prediccion

---

## Conclusion

Si todas las pruebas pasan:

- [x] Sistema IoT funcionando end-to-end
- [x] Datos fluyendo en tiempo real
- [x] Modelo ML haciendo predicciones
- [x] Visualizacion en dashboard
- [x] Control automatico de valvula

**El sistema esta listo para la presentacion!**
