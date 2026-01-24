# 06 - Modelo de Machine Learning

## Resumen

El sistema utiliza un modelo **Random Forest Classifier** entrenado con datos climáticos históricos de Jerusalén, Ecuador. El modelo predice si se debe regar o no basándose en 7 variables.

| Métrica | Valor |
|---------|-------|
| **Accuracy** | 99.83% |
| **Precision** | 98.92% |
| **Recall** | 99.46% |
| **F1-Score** | 99.19% |
| **ROC-AUC** | 1.0 |

---

## Arquitectura

```
    ENTRENAMIENTO (Offline)                      INFERENCIA (Tiempo Real)
    =======================                      ========================

    +------------------+                         +------------------+
    | Datos Históricos |                         |    Node-RED      |
    | Open-Meteo API   |                         |                  |
    | Jerusalén 2024-26|                         | sensores + clima |
    +--------+---------+                         +--------+---------+
             |                                            |
             v                                            v
    +------------------+                         +------------------+
    | Simular Humedad  |                         | HTTP POST        |
    | Suelo (balance   |                         | /predict         |
    | hídrico)         |                         |                  |
    +--------+---------+                         +--------+---------+
             |                                            |
             v                                            v
    +------------------+                         +------------------+
    | Generar Labels   |                         |    API Flask     |
    | (criterios FAO)  |                         |    :5001         |
    +--------+---------+                         +--------+---------+
             |                                            |
             v                                            v
    +------------------+        +------------------+      |
    | Entrenar         |        |                  |      |
    | Random Forest    |------->| modelo.joblib   |------+
    | (scikit-learn)   |        |                  |
    +------------------+        +------------------+
```

---

## Datos de Entrenamiento

### Fuente de Datos

| Característica | Valor |
|----------------|-------|
| **Ubicación** | Jerusalén, Azuay, Ecuador |
| **Coordenadas** | -2.690425, -78.935117 |
| **Período** | 2 años (Enero 2024 - Enero 2026) |
| **Registros** | 17,424 (datos horarios) |
| **Fuente** | Open-Meteo Historical API |

### Variables Descargadas de Open-Meteo

- `temperature_2m` - Temperatura a 2 metros
- `relative_humidity_2m` - Humedad relativa
- `precipitation` - Precipitación por hora

### Simulación de Humedad del Suelo

Open-Meteo no provee datos de humedad del suelo para esta ubicación, por lo que se implementó un **modelo de balance hídrico** basado en:

- Ganancia por precipitación
- Pérdida por evapotranspiración (función de temperatura, hora, humedad ambiente)
- Pérdida por consumo de plantas
- Factor estacional (meses secos: junio-septiembre)

```python
# Modelo simplificado de balance hídrico
h_nueva = h_anterior + ganancia_lluvia - perdida_eto - perdida_plantas

# Donde:
# - ganancia_lluvia = precipitacion * 6.0 (% por mm)
# - perdida_eto = f(temperatura, humedad_ambiente, hora, mes)
# - perdida_plantas = 0.15% por hora
```

---

## Variables del Modelo (Features)

| Variable | Fuente | Importancia |
|----------|--------|-------------|
| **humedad_suelo** | Sensor/Simulado | 73.7% |
| **mes** | Sistema | 10.4% |
| **prob_lluvia** | Open-Meteo | 6.5% |
| **hora** | Sistema | 4.3% |
| **temperatura** | Sensor | 1.9% |
| **humedad_ambiente** | Sensor | 1.7% |
| **precipitacion** | Open-Meteo | 1.5% |

### Observaciones

1. La **humedad del suelo** es por lejos la variable más importante (73.7%)
2. El **mes** captura estacionalidad (épocas secas vs lluviosas)
3. La **probabilidad de lluvia** ayuda a evitar riegos innecesarios

---

## Criterios de Etiquetado (basados en FAO)

Las etiquetas de entrenamiento se generaron usando criterios agronómicos de FAO Irrigation Papers 56 y 33:

| Regla | Condición | Decisión | Justificación |
|-------|-----------|----------|---------------|
| 1 | humedad_suelo < 20% | REGAR | Punto de marchitez |
| 2 | humedad_suelo >= 80% | NO_REGAR | Riesgo encharcamiento |
| 3 | precipitacion > 0.5mm | NO_REGAR | Está lloviendo |
| 4 | precip_24h > 5mm | NO_REGAR | Llovió recientemente |
| 5 | prob_lluvia > 70% | NO_REGAR | Va a llover |
| 6 | humedad < 35% + temp > 28°C + hora 5-9 | REGAR | Estrés térmico |
| 7 | humedad < 40% + hora 5-8 + prob_lluvia < 50% | REGAR | Riego preventivo mañana |
| 8 | humedad < 50% + temp > 30°C | REGAR | Calor extremo |

---

## Parámetros del Modelo

```python
RF_PARAMS = {
    "n_estimators": 100,        # Número de árboles
    "max_depth": 10,            # Profundidad máxima
    "min_samples_split": 5,     # Mínimo para dividir nodo
    "min_samples_leaf": 2,      # Mínimo en hojas
    "random_state": 42,         # Reproducibilidad
    "n_jobs": -1,               # Usar todos los cores
    "class_weight": "balanced"  # Manejar desbalance de clases
}
```

---

## Resultados del Entrenamiento

### Distribución de Clases

| Clase | Cantidad | Porcentaje |
|-------|----------|------------|
| NO_REGAR | 15,584 | 89.4% |
| REGAR | 1,840 | 10.6% |

### Métricas

```
              precision    recall  f1-score   support

    NO_REGAR       1.00      1.00      1.00      3117
       REGAR       0.99      0.99      0.99       368

    accuracy                           1.00      3485
```

### Matriz de Confusión

```
                 Predicho
              NO_REGAR  REGAR
Real NO_REGAR    3113       4
Real REGAR          2     366
```

### Validación Cruzada (5-fold)

| Métrica | Media | Desv. Estándar |
|---------|-------|----------------|
| Accuracy | 0.998 | ±0.001 |
| F1-Score | 0.992 | ±0.005 |
| Precision | 0.992 | ±0.009 |
| Recall | 0.993 | ±0.009 |

---

## API Flask

### Configuración

- **Puerto:** 5001 (evita conflicto con AirPlay en macOS)
- **Framework:** Flask
- **Modelo:** Cargado al iniciar desde `models/modelo_riego.joblib`

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Estado del servicio |
| GET | `/features` | Features requeridas |
| POST | `/predict` | Hacer predicción |
| POST | `/predict/batch` | Predicción en lote |
| GET | `/model/info` | Info del modelo |

### Ejemplo de Uso

```bash
# Iniciar API
cd python/
uv run python 03_api_flask.py

# Hacer predicción
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

### Respuesta

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

## Pruebas del Modelo

| Escenario | Humedad | Condiciones | Decisión | Confianza |
|-----------|---------|-------------|----------|-----------|
| Suelo crítico | 15% | Sin lluvia | REGAR | 97.8% |
| Suelo seco | 30% | Calor, sin lluvia | REGAR | 57.3% |
| Seco + lluvia próxima | 32% | Prob lluvia 85% | NO_REGAR | 94.8% |
| Suelo húmedo | 65% | Normal | NO_REGAR | 99.4% |
| Lloviendo | 55% | Precipitación 5.5mm | NO_REGAR | 100% |
| Post-lluvia | 75% | Recién llovió | NO_REGAR | 100% |

---

## Integración con Node-RED

El flujo de Node-RED llama a la API Flask cada 1 minuto:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Inject       │───▶│ Preparar     │───▶│ HTTP POST    │───▶│ Procesar     │
│ cada 1 min   │    │ JSON         │    │ :5001/predict│    │ respuesta    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

El nodo "Preparar JSON" construye el payload:

```javascript
msg.payload = {
    humedad_suelo: sensores.humedad_suelo,
    temperatura: sensores.temperatura,
    humedad_ambiente: sensores.humedad_ambiente,
    precipitacion: clima.precipitacion_actual || 0,
    prob_lluvia: clima.max_prob_lluvia_24h || 0,
    hora: new Date().getHours(),
    mes: new Date().getMonth() + 1
};
```

---

## Archivos

```
python/
├── 01_descargar_datos.py      # Descarga datos Open-Meteo + simula humedad
├── 02_entrenar_modelo.py      # Entrena Random Forest
├── 03_api_flask.py            # API REST
├── pyproject.toml             # Dependencias (uv)
├── dataset/
│   ├── datos_historicos_jerusalen.csv  # 17,424 registros
│   └── parametros_riego.txt            # Parámetros FAO
└── models/
    ├── modelo_riego.joblib    # Modelo serializado
    └── metricas.txt           # Métricas de evaluación
```

---

## Ejecución

```bash
cd python/

# 1. Descargar datos (solo primera vez o para re-entrenar)
uv run python 01_descargar_datos.py

# 2. Entrenar modelo (solo primera vez o para re-entrenar)
uv run python 02_entrenar_modelo.py

# 3. Iniciar API (siempre que se use el sistema)
uv run python 03_api_flask.py
```

---

## Siguiente Paso

Ver `07_PRUEBAS.md` para verificar el funcionamiento end-to-end del sistema.
