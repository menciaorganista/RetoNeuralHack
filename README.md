# MyE – Sistema Inteligente de Analisis de Trafico con Imagenes UAV

MyE es un sistema inteligente para el análisis automático del tráfico a partir de imágenes aéreas capturadas mediante UAV (drones).
El sistema combina visión artificial, métricas de movilidad y generación de evidencia criptográfica para producir resultados trazables, auditables e inmutables, orientados a aplicaciones de Smart Cities y planificación urbana.

---

## Que hace el sistema

1. Detección automática de vehéculos con YOLOv8 entrenado en Kaggle.
2. Clasificación de tipología de vehículo (coche, camión, moto, bicicleta, autobús).
3. Cálculo de métricas:
   - Conteo de vehiculos
   - Densidad de tráfico
   - Ocupación de la escena
   - Impacto ponderado por tipo de vehículo
   - Índice de congestion
4. Generación de evidencia:
   - Hash SHA-256
   - Marca temporal UTC
5. Visualización web con Streamlit.

---

El modelo entrenado no se incluye en el repositorio.

Descargar el archivo MyE_best.pt desde:
https://github.com/menciaorganista/RetoNeuralHack/releases/tag/v1.0-model

Ubicar el archivo en:
weights/MyE_best.pt

El entrenamiento del modelo se documento en:
notebook/train_kaggle.ipynb

---

## Instalación

git clone https://github.com/menciaorganista/RetoNeuralHack.git
cd RetoNeuralHack
pip install -r requirements.txt

---

## Ejecución

streamlit run src/app/app.py

---
