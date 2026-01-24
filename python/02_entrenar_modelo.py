"""
02 - Entrenar Modelo de Machine Learning
=========================================
Sistema IoT de Riego Inteligente para Pastizales
UTPL - Maestria en IA Aplicada

Este script entrena un modelo Random Forest para predecir
la necesidad de riego basado en datos climaticos y de sensores.

Algoritmo: Random Forest Classifier
- Robusto contra overfitting
- Maneja bien variables numericas
- Permite ver importancia de features
- Validado en proyectos similares (ver GitHub)

Autor: Luis
Fecha: Enero 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
import joblib

# =============================================================================
# CONFIGURACION
# =============================================================================

DATA_DIR = Path(__file__).parent / "dataset"
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Features a utilizar para el modelo
FEATURES = [
    "humedad_suelo",
    "temperatura",
    "humedad_ambiente",
    "precipitacion",
    "prob_lluvia",
    "hora",
    "mes",
]

# Variable objetivo
TARGET = "regar"

# Parametros del modelo Random Forest
RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": 42,
    "n_jobs": -1,
    "class_weight": "balanced",  # Manejar desbalance de clases
}


def cargar_datos() -> pd.DataFrame:
    """Carga el dataset de entrenamiento."""
    archivo = DATA_DIR / "datos_historicos_paute.csv"

    if not archivo.exists():
        raise FileNotFoundError(
            f"No se encontro el dataset en {archivo}\n"
            "Ejecuta primero: uv run 01_descargar_datos.py"
        )

    df = pd.read_csv(archivo)
    print(f"Dataset cargado: {len(df):,} registros")

    return df


def preparar_datos(df: pd.DataFrame) -> tuple:
    """
    Prepara los datos para entrenamiento.

    Returns:
        X: Features
        y: Target
        feature_names: Nombres de las features
    """
    # Verificar que todas las features existen
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise ValueError(f"Features faltantes en dataset: {missing}")

    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    print(f"\nFeatures utilizadas: {FEATURES}")
    print(f"Registros: {len(X):,}")
    print(f"Distribucion target: NO_REGAR={sum(y == 0):,}, REGAR={sum(y == 1):,}")

    return X, y, FEATURES


def entrenar_modelo(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Entrena el modelo Random Forest con validacion cruzada.

    Returns:
        modelo: Modelo entrenado
        metricas: Diccionario con metricas de evaluacion
        X_test, y_test: Datos de prueba
    """
    print("\n" + "=" * 60)
    print("ENTRENAMIENTO DEL MODELO")
    print("=" * 60)

    # Split train/test estratificado
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nConjunto de entrenamiento: {len(X_train):,} registros")
    print(f"Conjunto de prueba: {len(X_test):,} registros")

    # Crear modelo
    modelo = RandomForestClassifier(**RF_PARAMS)

    # Validacion cruzada (5-fold)
    print("\nValidacion cruzada (5-fold)...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    cv_scores = {
        "accuracy": cross_val_score(
            modelo, X_train, y_train, cv=cv, scoring="accuracy"
        ),
        "f1": cross_val_score(modelo, X_train, y_train, cv=cv, scoring="f1"),
        "precision": cross_val_score(
            modelo, X_train, y_train, cv=cv, scoring="precision"
        ),
        "recall": cross_val_score(modelo, X_train, y_train, cv=cv, scoring="recall"),
    }

    print(
        f"  Accuracy:  {cv_scores['accuracy'].mean():.3f} (+/- {cv_scores['accuracy'].std() * 2:.3f})"
    )
    print(
        f"  F1-Score:  {cv_scores['f1'].mean():.3f} (+/- {cv_scores['f1'].std() * 2:.3f})"
    )
    print(
        f"  Precision: {cv_scores['precision'].mean():.3f} (+/- {cv_scores['precision'].std() * 2:.3f})"
    )
    print(
        f"  Recall:    {cv_scores['recall'].mean():.3f} (+/- {cv_scores['recall'].std() * 2:.3f})"
    )

    # Entrenar modelo final
    print("\nEntrenando modelo final...")
    modelo.fit(X_train, y_train)

    # Evaluar en test set
    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]

    metricas = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "cv_accuracy_mean": cv_scores["accuracy"].mean(),
        "cv_accuracy_std": cv_scores["accuracy"].std(),
    }

    return modelo, metricas, X_test, y_test, y_pred


def mostrar_resultados(metricas: dict, y_test, y_pred, modelo, feature_names: list):
    """Muestra resultados detallados del entrenamiento."""

    print("\n" + "=" * 60)
    print("RESULTADOS EN CONJUNTO DE PRUEBA")
    print("=" * 60)

    print(f"\nMetricas:")
    print(
        f"  Accuracy:  {metricas['accuracy']:.3f} ({metricas['accuracy'] * 100:.1f}%)"
    )
    print(f"  Precision: {metricas['precision']:.3f}")
    print(f"  Recall:    {metricas['recall']:.3f}")
    print(f"  F1-Score:  {metricas['f1']:.3f}")
    print(f"  ROC-AUC:   {metricas['roc_auc']:.3f}")

    print("\nReporte de Clasificacion:")
    print(classification_report(y_test, y_pred, target_names=["NO_REGAR", "REGAR"]))

    print("Matriz de Confusion:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"                 Predicho")
    print(f"              NO_REGAR  REGAR")
    print(f"Real NO_REGAR   {cm[0, 0]:5d}   {cm[0, 1]:5d}")
    print(f"Real REGAR      {cm[1, 0]:5d}   {cm[1, 1]:5d}")

    # Importancia de features
    print("\n" + "=" * 60)
    print("IMPORTANCIA DE VARIABLES")
    print("=" * 60)

    importancias = pd.DataFrame(
        {"feature": feature_names, "importancia": modelo.feature_importances_}
    ).sort_values("importancia", ascending=False)

    print("\n" + importancias.to_string(index=False))

    return importancias


def guardar_modelo(modelo, feature_names: list, metricas: dict):
    """Guarda el modelo entrenado y metadata."""

    # Guardar modelo
    modelo_data = {
        "modelo": modelo,
        "features": feature_names,
        "metricas": metricas,
        "version": "1.0",
        "algoritmo": "RandomForestClassifier",
        "parametros": RF_PARAMS,
    }

    modelo_file = MODELS_DIR / "modelo_riego.joblib"
    joblib.dump(modelo_data, modelo_file)
    print(f"\nModelo guardado en: {modelo_file}")

    # Guardar metricas en texto
    metricas_file = MODELS_DIR / "metricas.txt"
    with open(metricas_file, "w") as f:
        f.write("METRICAS DEL MODELO DE RIEGO\n")
        f.write("=" * 40 + "\n")
        f.write(f"Algoritmo: Random Forest Classifier\n")
        f.write(f"Features: {feature_names}\n\n")
        f.write("Metricas en Test Set:\n")
        for key, value in metricas.items():
            f.write(f"  {key}: {value:.4f}\n")
    print(f"Metricas guardadas en: {metricas_file}")

    return modelo_file


def main():
    """Funcion principal."""
    print("\n" + "=" * 60)
    print("ENTRENAMIENTO DE MODELO - RANDOM FOREST")
    print("Sistema de Riego IoT para Pastizales")
    print("=" * 60)

    try:
        # Cargar datos
        df = cargar_datos()

        # Preparar datos
        X, y, feature_names = preparar_datos(df)

        # Entrenar
        modelo, metricas, X_test, y_test, y_pred = entrenar_modelo(X, y)

        # Mostrar resultados
        importancias = mostrar_resultados(
            metricas, y_test, y_pred, modelo, feature_names
        )

        # Guardar
        modelo_file = guardar_modelo(modelo, feature_names, metricas)

        print("\n" + "=" * 60)
        print("ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\nAccuracy: {metricas['accuracy'] * 100:.1f}%")
        print(f"F1-Score: {metricas['f1']:.3f}")
        print(f"\nModelo listo para usar en: {modelo_file}")

    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
