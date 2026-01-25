"""
03 - API Flask para Predicciones
=================================
Sistema IoT de Riego Inteligente para Pastizales
UTPL - Maestria en IA Aplicada

Esta API expone el modelo de ML para que Node-RED
pueda hacer predicciones en tiempo real.

Endpoints:
- GET  /health    - Estado del servicio
- GET  /features  - Features requeridas
- POST /predict   - Hacer prediccion

Autor: Luis
Fecha: Enero 2026
"""

from flask import Flask, request, jsonify
from pathlib import Path
import joblib
import numpy as np
from datetime import datetime

# =============================================================================
# CONFIGURACION
# =============================================================================

MODELS_DIR = Path(__file__).parent / "models"
MODEL_FILE = MODELS_DIR / "modelo_riego.joblib"

app = Flask(__name__)

# Variable global para el modelo
MODELO_DATA = None


def cargar_modelo():
    """Carga el modelo al iniciar la aplicacion."""
    global MODELO_DATA

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"No se encontro el modelo en {MODEL_FILE}\n"
            "Ejecuta primero:\n"
            "  uv run 01_descargar_datos.py\n"
            "  uv run 02_entrenar_modelo.py"
        )

    print(f"Cargando modelo desde {MODEL_FILE}...")
    MODELO_DATA = joblib.load(MODEL_FILE)
    print(f"Modelo cargado correctamente")
    print(f"  Algoritmo: {MODELO_DATA.get('algoritmo', 'Unknown')}")
    print(f"  Features: {MODELO_DATA['features']}")
    print(f"  Accuracy: {MODELO_DATA['metricas']['accuracy']:.1%}")


# =============================================================================
# ENDPOINTS
# =============================================================================


@app.route("/", methods=["GET"])
def index():
    """Pagina principal con informacion de la API."""
    return jsonify(
        {
            "nombre": "API de Prediccion de Riego",
            "version": MODELO_DATA.get("version", "1.0") if MODELO_DATA else "N/A",
            "descripcion": "Sistema IoT de Riego Inteligente para Pastizales",
            "endpoints": {
                "GET /": "Esta informacion",
                "GET /health": "Estado del servicio",
                "GET /features": "Features requeridas por el modelo",
                "POST /predict": "Hacer prediccion de riego",
            },
        }
    )


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de salud para verificar que el servicio esta activo."""
    if MODELO_DATA is None:
        return jsonify({"status": "error", "message": "Modelo no cargado"}), 500

    return jsonify(
        {
            "status": "ok",
            "model_loaded": True,
            "model_version": MODELO_DATA.get("version", "1.0"),
            "accuracy": round(MODELO_DATA["metricas"]["accuracy"], 3),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/features", methods=["GET"])
def get_features():
    """Retorna las features esperadas por el modelo."""
    if MODELO_DATA is None:
        return jsonify({"error": "Modelo no cargado"}), 500

    return jsonify(
        {
            "features": MODELO_DATA["features"],
            "descripcion": {
                "humedad_suelo": "Humedad del suelo en % (0-100)",
                "temperatura": "Temperatura en grados Celsius",
                "humedad_ambiente": "Humedad relativa del aire en % (0-100)",
                "precipitacion": "Precipitacion actual en mm",
                "prob_lluvia": "Probabilidad de lluvia proximas 24h en % (0-100)",
                "hora": "Hora del dia (0-23)",
                "mes": "Mes del ano (1-12)",
            },
            "ejemplo": {
                "humedad_suelo": 35.0,
                "temperatura": 24.5,
                "humedad_ambiente": 65.0,
                "precipitacion": 0.0,
                "prob_lluvia": 30.0,
                "hora": 7,
                "mes": 6,
            },
        }
    )


@app.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint de prediccion.

    Espera JSON con las features del modelo:
    {
        "humedad_suelo": 35.0,
        "temperatura": 24.5,
        "humedad_ambiente": 65.0,
        "precipitacion": 0.0,
        "prob_lluvia": 30.0,
        "hora": 7,
        "mes": 6
    }

    Retorna:
    {
        "decision": "REGAR",
        "decision_int": 1,
        "probabilidad": 0.87,
        "confianza": 87.0,
        "inputs": {...}
    }
    """
    if MODELO_DATA is None:
        return jsonify({"error": "Modelo no cargado"}), 500

    try:
        data = request.get_json()

        if data is None:
            return jsonify(
                {"error": "No se recibio JSON. Usa Content-Type: application/json"}
            ), 400

        features = MODELO_DATA["features"]
        modelo = MODELO_DATA["modelo"]

        # Validar campos requeridos
        missing = [f for f in features if f not in data]
        if missing:
            return jsonify(
                {
                    "error": f"Campos requeridos faltantes: {missing}",
                    "campos_requeridos": features,
                }
            ), 400

        # Validar tipos y rangos
        for feature in features:
            value = data[feature]
            if not isinstance(value, (int, float)):
                return jsonify(
                    {
                        "error": f"Campo '{feature}' debe ser numerico, recibido: {type(value).__name__}"
                    }
                ), 400

        # Crear DataFrame con nombres de features (evita warning de sklearn)
        import pandas as pd

        X = pd.DataFrame([[float(data[f]) for f in features]], columns=features)

        # Predecir
        prediccion = modelo.predict(X)[0]
        probabilidades = modelo.predict_proba(X)[0]

        # Probabilidad de la clase predicha
        prob_no_regar = probabilidades[0]
        prob_regar = probabilidades[1]
        confianza = probabilidades[prediccion]

        resultado = {
            "decision": "REGAR" if prediccion == 1 else "NO_REGAR",
            "decision_int": int(prediccion),
            "probabilidad_regar": round(float(prob_regar), 3),
            "probabilidad_no_regar": round(float(prob_no_regar), 3),
            "confianza": round(float(confianza) * 100, 1),
            "inputs": {f: data[f] for f in features},
            "timestamp": datetime.now().isoformat(),
        }

        # Log para debugging
        print(
            f"[PREDICCION] {resultado['decision']} (confianza: {resultado['confianza']}%)"
        )

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e), "tipo": type(e).__name__}), 500


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Prediccion en lote para multiples registros.

    Espera JSON con lista de registros:
    {
        "datos": [
            {"humedad_suelo": 35, "temperatura": 24, ...},
            {"humedad_suelo": 50, "temperatura": 20, ...}
        ]
    }
    """
    if MODELO_DATA is None:
        return jsonify({"error": "Modelo no cargado"}), 500

    try:
        data = request.get_json()

        if "datos" not in data:
            return jsonify(
                {"error": "Se requiere campo 'datos' con lista de registros"}
            ), 400

        registros = data["datos"]
        features = MODELO_DATA["features"]
        modelo = MODELO_DATA["modelo"]

        resultados = []
        for i, registro in enumerate(registros):
            # Validar campos
            missing = [f for f in features if f not in registro]
            if missing:
                resultados.append({"index": i, "error": f"Campos faltantes: {missing}"})
                continue

            # Predecir
            X = np.array([[float(registro[f]) for f in features]])
            prediccion = modelo.predict(X)[0]
            probabilidades = modelo.predict_proba(X)[0]

            resultados.append(
                {
                    "index": i,
                    "decision": "REGAR" if prediccion == 1 else "NO_REGAR",
                    "decision_int": int(prediccion),
                    "confianza": round(float(probabilidades[prediccion]) * 100, 1),
                }
            )

        return jsonify({"total": len(registros), "resultados": resultados})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/model/info", methods=["GET"])
def model_info():
    """Retorna informacion detallada del modelo."""
    if MODELO_DATA is None:
        return jsonify({"error": "Modelo no cargado"}), 500

    return jsonify(
        {
            "version": MODELO_DATA.get("version", "1.0"),
            "algoritmo": MODELO_DATA.get("algoritmo", "RandomForestClassifier"),
            "features": MODELO_DATA["features"],
            "metricas": {
                k: round(v, 4) if isinstance(v, float) else v
                for k, v in MODELO_DATA["metricas"].items()
            },
            "parametros": MODELO_DATA.get("parametros", {}),
        }
    )


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Funcion principal para ejecutar la API."""
    print("\n" + "=" * 60)
    print("API DE PREDICCION DE RIEGO")
    print("Sistema IoT para Pastizales - UTPL")
    print("=" * 60)

    # Cargar modelo
    cargar_modelo()

    print("\n" + "-" * 60)
    print("ENDPOINTS DISPONIBLES:")
    print("-" * 60)
    print("  GET  /           - Informacion de la API")
    print("  GET  /health     - Estado del servicio")
    print("  GET  /features   - Features requeridas")
    print("  POST /predict    - Hacer prediccion")
    print("  POST /predict/batch - Prediccion en lote")
    print("  GET  /model/info - Informacion del modelo")
    print("-" * 60)
    print("\nIniciando servidor en http://localhost:5001")
    print("Presiona Ctrl+C para detener\n")

    # Ejecutar servidor (puerto 5001 para evitar conflicto con AirPlay en macOS)
    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()
