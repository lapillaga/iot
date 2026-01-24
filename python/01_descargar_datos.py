"""
01 - Descargar Datos Historicos de Open-Meteo
==============================================
Sistema IoT de Riego Inteligente para Pastizales
UTPL - Maestria en IA Aplicada

Este script descarga datos climaticos historicos de Jerusalen, Ecuador
usando la API de Open-Meteo y genera etiquetas para entrenamiento.

Fuentes cientificas:
- FAO Irrigation and Drainage Paper 56 (ETo y coeficientes)
- FAO Paper 33 (Respuesta de cultivos al agua)
- Factor de agotamiento (p) para pastos: 0.50-0.60

Autor: Luis
Fecha: Enero 2026
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# CONFIGURACION
# =============================================================================

# Coordenadas de Jerusalén, Azuay, Ecuador
LATITUD = -2.690425
LONGITUD = -78.935117
TIMEZONE = "America/Guayaquil"

# Directorio de salida
OUTPUT_DIR = Path(__file__).parent / "dataset"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# PARAMETROS AGRONOMICOS (basados en FAO)
# =============================================================================

PARAMETROS_RIEGO = {
    # Umbrales de humedad del suelo (%)
    # Basado en FAO Paper 56, Tabla 22 para pastos
    "HUMEDAD_CRITICA": 20,  # Regar urgente - punto de marchitez cercano
    "HUMEDAD_BAJA": 35,  # Regar si no va a llover
    "HUMEDAD_OPTIMA_MIN": 40,  # Limite inferior optimo
    "HUMEDAD_OPTIMA_MAX": 70,  # Limite superior optimo
    "HUMEDAD_EXCESO": 80,  # No regar - riesgo de encharcamiento
    # Umbrales de precipitacion (mm)
    "LLUVIA_RECIENTE_MIN": 5,  # Si llovio esto en ultimas horas, no regar
    "PROB_LLUVIA_ESPERAR": 70,  # Si prob > 70%, esperar
    # Umbrales de temperatura (C)
    # Basado en FAO - ETo aumenta con temperatura
    "TEMP_ALTA": 28,  # Aumenta evapotranspiracion
    "TEMP_BAJA": 12,  # Reduce evapotranspiracion
    # Horas optimas de riego (evitar evaporacion)
    "HORA_RIEGO_INICIO": 5,  # 5 AM
    "HORA_RIEGO_FIN": 9,  # 9 AM
    # Factor de agotamiento para pastos de clima templado
    # FAO Paper 56, Tabla 22: Grazing Pasture p=0.60
    "FACTOR_AGOTAMIENTO": 0.55,
}


def descargar_datos_historicos(fecha_inicio: str, fecha_fin: str) -> dict:
    """
    Descarga datos historicos de Open-Meteo Historical Weather API.

    Args:
        fecha_inicio: Fecha inicio en formato YYYY-MM-DD
        fecha_fin: Fecha fin en formato YYYY-MM-DD

    Returns:
        dict con datos de la API
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
        ],
        "timezone": TIMEZONE,
    }

    print(f"Descargando datos desde {fecha_inicio} hasta {fecha_fin}...")
    print(f"Ubicacion: Jerusalen, Ecuador ({LATITUD}, {LONGITUD})")

    response = requests.get(url, params=params, timeout=60)

    if response.status_code != 200:
        raise Exception(f"Error en API: {response.status_code} - {response.text}")

    return response.json()


def procesar_datos(data: dict) -> pd.DataFrame:
    """
    Convierte la respuesta de la API a DataFrame con features adicionales.

    Args:
        data: Respuesta JSON de Open-Meteo

    Returns:
        DataFrame con datos procesados
    """
    hourly = data["hourly"]

    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(hourly["time"]),
            "temperatura": hourly["temperature_2m"],
            "humedad_ambiente": hourly["relative_humidity_2m"],
            "precipitacion": hourly["precipitation"],
        }
    )

    # Features temporales
    df["hora"] = df["timestamp"].dt.hour
    df["mes"] = df["timestamp"].dt.month
    df["dia_semana"] = df["timestamp"].dt.dayofweek
    df["dia_del_anio"] = df["timestamp"].dt.dayofyear

    # Precipitacion acumulada ultimas 24 horas
    df["precip_24h"] = df["precipitacion"].rolling(window=24, min_periods=1).sum()

    # Calcular probabilidad de lluvia simulada basada en patrones
    # (En produccion vendria de la API de pronostico)
    df["prob_lluvia"] = calcular_prob_lluvia_simulada(df)

    # Temperatura promedio ultimas 6 horas
    df["temp_promedio_6h"] = df["temperatura"].rolling(window=6, min_periods=1).mean()

    # SIMULAR humedad del suelo
    # Open-Meteo no provee soil_moisture para esta ubicacion
    # Usamos un modelo fisico simplificado basado en balance hidrico
    df["humedad_suelo"] = simular_humedad_suelo(df)

    return df


def simular_humedad_suelo(df: pd.DataFrame) -> pd.Series:
    """
    Simula la humedad del suelo usando un modelo de balance hidrico simplificado.

    Modelo:
    - La humedad aumenta con la precipitacion
    - La humedad disminuye con la evapotranspiracion (funcion de temp y hora)
    - La humedad tiene inercia (cambia gradualmente)

    Basado en:
    - FAO Paper 56: ETo = f(temperatura, humedad, radiacion)
    - Capacidad de campo tipica para suelos de sierra: 35-45%
    - Punto de marchitez: 15-20%

    NOTA: Se ajustan parametros para generar un dataset balanceado
    que represente escenarios realistas de pastizales que SI necesitan riego.

    Returns:
        Serie con humedad del suelo simulada (0-100%)
    """
    n = len(df)
    humedad = np.zeros(n)

    # Parametros del modelo - AJUSTADOS para mayor variabilidad
    CAPACIDAD_CAMPO = 70.0  # % - maximo que retiene el suelo
    PUNTO_MARCHITEZ = 12.0  # % - minimo antes de estres severo
    HUMEDAD_INICIAL = 40.0  # % - valor inicial mas bajo

    # Tasas (por hora) - AUMENTAMOS evapotranspiracion
    TASA_INFILTRACION = 6.0  # % por mm de lluvia (reducido)
    TASA_DRENAJE = 0.8  # % por hora si esta sobre capacidad campo

    humedad[0] = HUMEDAD_INICIAL

    for i in range(1, n):
        h_anterior = humedad[i - 1]
        precip = df["precipitacion"].iloc[i]
        temp = df["temperatura"].iloc[i]
        hum_amb = df["humedad_ambiente"].iloc[i]
        hora = df["hora"].iloc[i]
        mes = df["mes"].iloc[i]

        # 1. Ganancia por precipitacion
        ganancia = precip * TASA_INFILTRACION

        # 2. Perdida por evapotranspiracion (AUMENTADA)
        # Mayor evaporacion con: alta temp, baja humedad ambiente, horas de sol
        es_dia = 6 <= hora <= 18
        factor_solar = 2.0 if es_dia else 0.4  # Aumentado
        factor_temp = max(0, (temp - 8) / 15)  # Mas sensible a temperatura
        factor_humedad = max(0.2, (100 - hum_amb) / 80)  # Siempre algo de evaporacion

        # Factor estacional - meses secos en Ecuador (jun-sep) pierden mas agua
        es_estacion_seca = mes in [6, 7, 8, 9]
        factor_estacional = 1.8 if es_estacion_seca else 1.0

        perdida_eto = (
            0.6 * factor_solar * factor_temp * factor_humedad * factor_estacional
        )

        # 3. Drenaje si esta sobre capacidad de campo
        if h_anterior > CAPACIDAD_CAMPO:
            perdida_drenaje = TASA_DRENAJE
        else:
            perdida_drenaje = 0

        # 4. Perdida base por consumo de plantas (pastos consumen agua)
        perdida_plantas = 0.15  # % por hora

        # 5. Calcular nueva humedad
        h_nueva = (
            h_anterior + ganancia - perdida_eto - perdida_drenaje - perdida_plantas
        )

        # 6. Limitar a rango fisico
        h_nueva = max(PUNTO_MARCHITEZ * 0.6, min(CAPACIDAD_CAMPO * 1.1, h_nueva))

        # 7. Agregar ruido para simular variabilidad natural (aumentado)
        ruido = np.random.normal(0, 2.5)
        h_nueva = max(8, min(80, h_nueva + ruido))

        humedad[i] = h_nueva

    return pd.Series(humedad, index=df.index)


def calcular_prob_lluvia_simulada(df: pd.DataFrame) -> pd.Series:
    """
    Simula probabilidad de lluvia basada en patrones historicos.
    En produccion, esto vendria de la API de pronostico.

    Logica: Si llovio recientemente o hay alta humedad ambiente,
    hay mayor probabilidad de lluvia.
    """
    prob = pd.Series(index=df.index, dtype=float)

    # Factores que aumentan probabilidad
    # 1. Humedad ambiente alta
    prob = (df["humedad_ambiente"] - 50).clip(0, 50)  # 0-50 base

    # 2. Precipitacion reciente aumenta probabilidad
    prob += (df["precipitacion"].rolling(window=6, min_periods=1).sum() * 5).clip(0, 30)

    # 3. Patron estacional (meses lluviosos en Ecuador: feb-may, oct-nov)
    meses_lluviosos = df["mes"].isin([2, 3, 4, 5, 10, 11])
    prob = prob + meses_lluviosos * 15

    # Normalizar a 0-100
    prob = prob.clip(0, 100)

    return prob


def generar_etiquetas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera etiquetas (REGAR=1, NO_REGAR=0) basadas en criterios agronomicos.

    Criterios basados en:
    - FAO Irrigation and Drainage Paper 56
    - Factor de agotamiento (p) para pastos: 0.55-0.60
    - Practicas de riego para pastizales en sierra andina

    Args:
        df: DataFrame con datos de sensores y clima

    Returns:
        DataFrame con columna 'regar' agregada
    """
    p = PARAMETROS_RIEGO

    def decidir_riego(row) -> int:
        humedad = row["humedad_suelo"]
        temp = row["temperatura"]
        precip = row["precipitacion"]
        precip_24h = row["precip_24h"]
        prob_lluvia = row["prob_lluvia"]
        hora = row["hora"]

        # REGLA 1: Suelo critico - REGAR URGENTE
        # Basado en punto de marchitez (wilting point)
        if humedad < p["HUMEDAD_CRITICA"]:
            return 1

        # REGLA 2: Suelo muy humedo o encharcado - NO REGAR
        if humedad >= p["HUMEDAD_EXCESO"]:
            return 0

        # REGLA 3: Esta lloviendo o llovio recientemente - NO REGAR
        if precip > 0.5 or precip_24h > p["LLUVIA_RECIENTE_MIN"]:
            return 0

        # REGLA 4: Alta probabilidad de lluvia - ESPERAR
        if prob_lluvia > p["PROB_LLUVIA_ESPERAR"]:
            return 0

        # REGLA 5: Suelo seco + calor + hora optima - REGAR
        if (
            humedad < p["HUMEDAD_BAJA"]
            and temp > p["TEMP_ALTA"]
            and p["HORA_RIEGO_INICIO"] <= hora <= p["HORA_RIEGO_FIN"]
        ):
            return 1

        # REGLA 6: Suelo seco + hora optima de manana - REGAR preventivo
        if (
            humedad < p["HUMEDAD_OPTIMA_MIN"]
            and p["HORA_RIEGO_INICIO"] <= hora <= p["HORA_RIEGO_FIN"]
            and prob_lluvia < 50
        ):
            return 1

        # REGLA 7: Suelo moderado pero calor extremo - REGAR
        if humedad < 50 and temp > 30:
            return 1

        # REGLA 8: Humedad en rango optimo - NO REGAR
        if p["HUMEDAD_OPTIMA_MIN"] <= humedad <= p["HUMEDAD_OPTIMA_MAX"]:
            return 0

        # DEFAULT: NO REGAR
        return 0

    df["regar"] = df.apply(decidir_riego, axis=1)

    return df


def mostrar_estadisticas(df: pd.DataFrame):
    """Muestra estadisticas del dataset generado."""
    print("\n" + "=" * 60)
    print("ESTADISTICAS DEL DATASET")
    print("=" * 60)

    print(f"\nRegistros totales: {len(df):,}")
    print(f"Periodo: {df['timestamp'].min()} a {df['timestamp'].max()}")

    print(f"\nDistribucion de clases:")
    distribucion = df["regar"].value_counts()
    print(
        f"  NO_REGAR (0): {distribucion.get(0, 0):,} ({distribucion.get(0, 0) / len(df) * 100:.1f}%)"
    )
    print(
        f"  REGAR (1):    {distribucion.get(1, 0):,} ({distribucion.get(1, 0) / len(df) * 100:.1f}%)"
    )

    print(f"\nEstadisticas de variables:")
    print(
        df[
            [
                "humedad_suelo",
                "temperatura",
                "humedad_ambiente",
                "precipitacion",
                "prob_lluvia",
            ]
        ]
        .describe()
        .round(2)
    )


def main():
    """Funcion principal."""
    print("\n" + "=" * 60)
    print("DESCARGA DE DATOS HISTORICOS - OPEN-METEO")
    print("Sistema de Riego IoT para Pastizales")
    print("=" * 60)

    # Calcular fechas (ultimos 2 anios - limite de API gratuita)
    fecha_fin = (datetime.now() - timedelta(days=5)).strftime(
        "%Y-%m-%d"
    )  # 5 dias atras (datos disponibles)
    fecha_inicio = (datetime.now() - timedelta(days=730)).strftime(
        "%Y-%m-%d"
    )  # 2 anios

    try:
        # Descargar datos
        data = descargar_datos_historicos(fecha_inicio, fecha_fin)
        print(f"Datos descargados correctamente")

        # Procesar
        df = procesar_datos(data)
        print(f"Datos procesados: {len(df)} registros horarios")

        # Generar etiquetas
        df = generar_etiquetas(df)
        print(f"Etiquetas generadas con criterios FAO")

        # Limpiar NaN
        df_clean = df.dropna()
        print(f"Registros validos despues de limpieza: {len(df_clean)}")

        # Mostrar estadisticas
        mostrar_estadisticas(df_clean)

        # Guardar
        output_file = OUTPUT_DIR / "datos_historicos_jerusalen.csv"
        df_clean.to_csv(output_file, index=False)
        print(f"\nDataset guardado en: {output_file}")

        # Guardar tambien parametros usados
        params_file = OUTPUT_DIR / "parametros_riego.txt"
        with open(params_file, "w") as f:
            f.write("PARAMETROS DE RIEGO UTILIZADOS\n")
            f.write("=" * 40 + "\n")
            f.write("Basados en FAO Irrigation Papers 56 y 33\n\n")
            for key, value in PARAMETROS_RIEGO.items():
                f.write(f"{key}: {value}\n")
        print(f"Parametros guardados en: {params_file}")

    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
