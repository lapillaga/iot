# 06 - Modelo de Machine Learning

## Estado Actual vs Objetivo

### Estado Actual: Reglas If/Else

Actualmente el sistema usa reglas programadas manualmente en Node-RED:

```javascript
if (humedad_suelo < 20) {
    decision = "REGAR";  // Suelo critico
}
else if (humedad_suelo < 35 && prob_lluvia > 70) {
    decision = "NO_REGAR";  // Esperar lluvia
}
// ... mas reglas
```

**Esto NO es Machine Learning**, son reglas deterministas.

### Objetivo: Modelo ML Real

Entrenar un modelo de Machine Learning que:
1. Aprenda de datos historicos
2. Generalice a situaciones nuevas
3. Mejore con mas datos

---

## Arquitectura del Modelo

```
    ENTRENAMIENTO (Offline)                      INFERENCIA (Tiempo Real)
    =======================                      ========================

    +------------------+                         +------------------+
    | Datos Historicos |                         |    Node-RED      |
    | Open-Meteo API   |                         |                  |
    | (2020-2024)      |                         | sensores + clima |
    +--------+---------+                         +--------+---------+
             |                                            |
             v                                            |
    +------------------+                                  |
    | Feature          |                                  |
    | Engineering      |                                  |
    | - humedad        |                                  |
    | - temperatura    |                                  |
    | - prob_lluvia    |                                  |
    | - hora, mes      |                                  |
    +--------+---------+                                  |
             |                                            |
             v                                            |
    +------------------+                                  |
    | Generar Labels   |                                  |
    | (criterios       |                                  |
    |  agronomicos)    |                                  |
    +--------+---------+                                  |
             |                                            |
             v                                            |
    +------------------+        +------------------+      |
    | Entrenar         |        |                  |      |
    | Random Forest    |------->| modelo.pkl      |      |
    | (scikit-learn)   |        | (serializado)   |      |
    +------------------+        +--------+---------+      |
                                         |                |
                                         v                v
                                +------------------+------+
                                |    API Flask     |
                                |                  |
                                | POST /predict    |
                                | {                |
                                |   humedad: 45,   |
                                |   temp: 23,      |
                                |   ...            |
                                | }                |
                                |                  |
                                | Response:        |
                                | {                |
                                |   decision: 1,   |
                                |   proba: 0.87    |
                                | }                |
                                +------------------+
                                         |
                                         v
                                +------------------+
                                |    Node-RED      |
                                | (HTTP Request)   |
                                +------------------+
                                         |
                                         v
                                +------------------+
                                |    ESP32         |
                                | (REGAR/NO_REGAR) |
                                +------------------+
```

---

## Paso a Paso

### Paso 1: Crear Estructura de Carpetas

```bash
mkdir -p python/dataset
mkdir -p python/models
```

Estructura final:
```
python/
├── 01_descargar_datos.py    # Descarga datos historicos
├── 02_entrenar_modelo.py    # Entrena el modelo
├── 03_api_flask.py          # API para predicciones
├── requirements.txt         # Dependencias
├── dataset/
│   └── datos_historicos.csv
└── models/
    └── modelo_riego.pkl
```

---

### Paso 2: Instalar Dependencias

Crear `python/requirements.txt`:

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
requests>=2.31.0
flask>=3.0.0
joblib>=1.3.0
```

Instalar:
```bash
cd python
pip install -r requirements.txt
```

---

### Paso 3: Descargar Datos Historicos

Usar la API Historical de Open-Meteo para obtener datos de Paute (2020-2024).

**Archivo:** `python/01_descargar_datos.py`

```python
"""
Descarga datos historicos de clima para Paute, Ecuador
usando la API de Open-Meteo Historical Weather
"""

import requests
import pandas as pd
from datetime import datetime, timedelta

# Coordenadas de Paute, Azuay, Ecuador
LATITUD = -2.78
LONGITUD = -78.76

def descargar_datos_historicos(fecha_inicio, fecha_fin):
    """
    Descarga datos historicos de Open-Meteo
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": LATITUD,
        "longitude": LONGITUD,
        "start_date": fecha_inicio,
        "end_date": fecha_fin,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "soil_moisture_0_to_1cm"
        ],
        "timezone": "America/Guayaquil"
    }
    
    print(f"Descargando datos desde {fecha_inicio} hasta {fecha_fin}...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error en API: {response.status_code}")
    
    return response.json()


def procesar_datos(data):
    """
    Convierte la respuesta de la API a DataFrame
    """
    hourly = data["hourly"]
    
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"]),
        "temperatura": hourly["temperature_2m"],
        "humedad_ambiente": hourly["relative_humidity_2m"],
        "precipitacion": hourly["precipitation"],
        "humedad_suelo_api": hourly["soil_moisture_0_to_1cm"]
    })
    
    # Agregar features temporales
    df["hora"] = df["timestamp"].dt.hour
    df["mes"] = df["timestamp"].dt.month
    df["dia_semana"] = df["timestamp"].dt.dayofweek
    
    return df


def generar_labels(df):
    """
    Genera etiquetas (REGAR=1, NO_REGAR=0) basadas en criterios agronomicos
    
    Criterios para pastizales en sierra ecuatoriana:
    - Humedad suelo < 30%: necesita riego
    - Humedad suelo >= 60%: no necesita
    - Entre 30-60%: depende de temperatura y precipitacion
    """
    def decidir_riego(row):
        # Normalizar humedad suelo (API da valores 0-0.5, convertir a 0-100)
        humedad_suelo = row["humedad_suelo_api"] * 200  # Aproximacion
        humedad_suelo = min(100, max(0, humedad_suelo))
        
        temp = row["temperatura"]
        precip = row["precipitacion"]
        hora = row["hora"]
        
        # Regla 1: Suelo muy seco -> REGAR
        if humedad_suelo < 25:
            return 1
        
        # Regla 2: Suelo humedo -> NO REGAR
        if humedad_suelo >= 60:
            return 0
        
        # Regla 3: Esta lloviendo -> NO REGAR
        if precip > 0.5:
            return 0
        
        # Regla 4: Suelo seco + calor + mejor hora -> REGAR
        if humedad_suelo < 40 and temp > 22 and 5 <= hora <= 9:
            return 1
        
        # Regla 5: Suelo moderado + calor extremo -> REGAR
        if humedad_suelo < 50 and temp > 28:
            return 1
        
        # Default: NO REGAR
        return 0
    
    df["humedad_suelo"] = df["humedad_suelo_api"] * 200
    df["humedad_suelo"] = df["humedad_suelo"].clip(0, 100)
    df["regar"] = df.apply(decidir_riego, axis=1)
    
    return df


def main():
    # Descargar ultimos 3 anios (Open-Meteo gratis limita a ~2 anios)
    fecha_fin = datetime.now().strftime("%Y-%m-%d")
    fecha_inicio = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    
    # Descargar
    data = descargar_datos_historicos(fecha_inicio, fecha_fin)
    
    # Procesar
    df = procesar_datos(data)
    
    # Generar labels
    df = generar_labels(df)
    
    # Limpiar NaN
    df = df.dropna()
    
    # Guardar
    df.to_csv("dataset/datos_historicos.csv", index=False)
    
    print(f"\nDataset creado: {len(df)} registros")
    print(f"Distribucion de clases:")
    print(df["regar"].value_counts())
    print(f"\nGuardado en: dataset/datos_historicos.csv")


if __name__ == "__main__":
    main()
```

Ejecutar:
```bash
python 01_descargar_datos.py
```

---

### Paso 4: Entrenar el Modelo

**Archivo:** `python/02_entrenar_modelo.py`

```python
"""
Entrena un modelo Random Forest para predecir necesidad de riego
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

def cargar_datos():
    """Carga el dataset"""
    df = pd.read_csv("dataset/datos_historicos.csv")
    print(f"Dataset cargado: {len(df)} registros")
    return df


def preparar_features(df):
    """Selecciona y prepara features para el modelo"""
    features = [
        "humedad_suelo",
        "temperatura",
        "humedad_ambiente",
        "precipitacion",
        "hora",
        "mes"
    ]
    
    X = df[features]
    y = df["regar"]
    
    return X, y, features


def entrenar_modelo(X, y):
    """Entrena Random Forest con validacion cruzada"""
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {len(X_train)} registros")
    print(f"Test set: {len(X_test)} registros")
    
    # Entrenar modelo
    modelo = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    # Validacion cruzada
    print("\nValidacion cruzada (5-fold)...")
    scores = cross_val_score(modelo, X_train, y_train, cv=5, scoring='f1')
    print(f"F1-Score: {scores.mean():.3f} (+/- {scores.std()*2:.3f})")
    
    # Entrenar modelo final
    modelo.fit(X_train, y_train)
    
    # Evaluar en test
    y_pred = modelo.predict(X_test)
    
    print("\n" + "="*50)
    print("RESULTADOS EN TEST SET")
    print("="*50)
    print("\nReporte de Clasificacion:")
    print(classification_report(y_test, y_pred, target_names=["NO_REGAR", "REGAR"]))
    
    print("\nMatriz de Confusion:")
    print(confusion_matrix(y_test, y_pred))
    
    return modelo


def analizar_importancia(modelo, features):
    """Muestra importancia de cada feature"""
    importancias = pd.DataFrame({
        'feature': features,
        'importancia': modelo.feature_importances_
    }).sort_values('importancia', ascending=False)
    
    print("\n" + "="*50)
    print("IMPORTANCIA DE VARIABLES")
    print("="*50)
    print(importancias.to_string(index=False))
    
    return importancias


def guardar_modelo(modelo, features):
    """Guarda el modelo entrenado"""
    modelo_data = {
        'modelo': modelo,
        'features': features
    }
    
    joblib.dump(modelo_data, "models/modelo_riego.pkl")
    print(f"\nModelo guardado en: models/modelo_riego.pkl")


def main():
    # Cargar datos
    df = cargar_datos()
    
    # Preparar features
    X, y, features = preparar_features(df)
    
    # Entrenar
    modelo = entrenar_modelo(X, y)
    
    # Analizar
    analizar_importancia(modelo, features)
    
    # Guardar
    guardar_modelo(modelo, features)
    
    print("\n" + "="*50)
    print("ENTRENAMIENTO COMPLETADO")
    print("="*50)


if __name__ == "__main__":
    main()
```

Ejecutar:
```bash
python 02_entrenar_modelo.py
```

Salida esperada:
```
Dataset cargado: 17520 registros

Train set: 14016 registros
Test set: 3504 registros

Validacion cruzada (5-fold)...
F1-Score: 0.892 (+/- 0.023)

==================================================
RESULTADOS EN TEST SET
==================================================

Reporte de Clasificacion:
              precision    recall  f1-score   support

   NO_REGAR       0.91      0.94      0.93      2456
      REGAR       0.86      0.79      0.82      1048

    accuracy                           0.90      3504

==================================================
IMPORTANCIA DE VARIABLES
==================================================
       feature  importancia
  humedad_suelo        0.42
    temperatura        0.23
          hora         0.14
 precipitacion        0.11
humedad_ambiente       0.06
           mes         0.04

Modelo guardado en: models/modelo_riego.pkl
```

---

### Paso 5: Crear API Flask

**Archivo:** `python/03_api_flask.py`

```python
"""
API Flask para servir predicciones del modelo de riego
"""

from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

# Cargar modelo al iniciar
print("Cargando modelo...")
modelo_data = joblib.load("models/modelo_riego.pkl")
MODELO = modelo_data["modelo"]
FEATURES = modelo_data["features"]
print(f"Modelo cargado. Features: {FEATURES}")


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de salud"""
    return jsonify({"status": "ok", "model": "loaded"})


@app.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint de prediccion
    
    Espera JSON:
    {
        "humedad_suelo": 45.0,
        "temperatura": 23.5,
        "humedad_ambiente": 68.0,
        "precipitacion": 0.0,
        "hora": 8,
        "mes": 6
    }
    
    Retorna:
    {
        "decision": "REGAR",
        "decision_int": 1,
        "probabilidad": 0.87,
        "confianza": 87
    }
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        for feature in FEATURES:
            if feature not in data:
                return jsonify({
                    "error": f"Campo requerido: {feature}"
                }), 400
        
        # Crear array de features en orden correcto
        X = np.array([[data[f] for f in FEATURES]])
        
        # Predecir
        prediccion = MODELO.predict(X)[0]
        probabilidad = MODELO.predict_proba(X)[0]
        
        # Probabilidad de la clase predicha
        prob_clase = probabilidad[prediccion]
        
        resultado = {
            "decision": "REGAR" if prediccion == 1 else "NO_REGAR",
            "decision_int": int(prediccion),
            "probabilidad": round(float(prob_clase), 3),
            "confianza": round(float(prob_clase) * 100, 1),
            "inputs": data
        }
        
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/features", methods=["GET"])
def get_features():
    """Retorna las features esperadas por el modelo"""
    return jsonify({
        "features": FEATURES,
        "ejemplo": {
            "humedad_suelo": 45.0,
            "temperatura": 23.5,
            "humedad_ambiente": 68.0,
            "precipitacion": 0.0,
            "hora": 8,
            "mes": 6
        }
    })


if __name__ == "__main__":
    print("\n" + "="*50)
    print("API de Prediccion de Riego")
    print("="*50)
    print(f"Endpoints:")
    print(f"  GET  /health   - Estado del servicio")
    print(f"  GET  /features - Features requeridas")
    print(f"  POST /predict  - Hacer prediccion")
    print("="*50 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
```

Ejecutar:
```bash
python 03_api_flask.py
```

Probar con curl:
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "humedad_suelo": 25,
    "temperatura": 28,
    "humedad_ambiente": 50,
    "precipitacion": 0,
    "hora": 8,
    "mes": 6
  }'
```

Respuesta:
```json
{
  "decision": "REGAR",
  "decision_int": 1,
  "probabilidad": 0.87,
  "confianza": 87.0,
  "inputs": {...}
}
```

---

### Paso 6: Integrar con Node-RED

Modificar el nodo "Modelo ML" en Node-RED para llamar a la API:

1. Reemplazar el nodo `function` "Modelo ML (Decision)" por un `http request`
2. O modificar la funcion para hacer HTTP request

**Nueva funcion para Node-RED:**

```javascript
// Obtener datos
var sensores = flow.get('ultimosDatos') || {};
var clima = flow.get('datosClima') || {};

if (!sensores.humedad_suelo) {
    node.status({fill:"yellow", shape:"ring", text:"Esperando datos"});
    return null;
}

// Preparar request para API Flask
msg.url = "http://localhost:5000/predict";
msg.method = "POST";
msg.headers = {"Content-Type": "application/json"};

var now = new Date();
msg.payload = {
    humedad_suelo: sensores.humedad_suelo,
    temperatura: sensores.temperatura,
    humedad_ambiente: sensores.humedad_ambiente,
    precipitacion: clima.precipitacion_actual || 0,
    hora: now.getHours(),
    mes: now.getMonth() + 1
};

return msg;
```

---

## Verificacion

1. API Flask corriendo: `http://localhost:5000/health`
2. Node-RED llamando a la API
3. ESP32 recibiendo decisiones del modelo ML real

---

## Siguiente Paso

Continuar con `07_PRUEBAS.md` para verificar el funcionamiento end-to-end.
