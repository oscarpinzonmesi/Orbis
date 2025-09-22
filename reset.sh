#!/bin/bash
# 🚨 ADVERTENCIA: Esto elimina TODO el contenido del proyecto
# Úsalo solo si estás seguro de empezar desde cero

echo "⚠️ Borrando proyecto y entornos virtuales..."

# Elimina el código del proyecto
rm -rf /opt/render/project/src/*

# Elimina entornos virtuales
rm -rf /opt/render/project/src/.venv
rm -rf venv
rm -rf .venv

# Elimina archivos de caché de Python
find /opt/render/project/src -type d -name "__pycache__" -exec rm -rf {} +
find /opt/render/project/src -type f -name "*.pyc" -delete

# Elimina dependencias instaladas en caché
pip cache purge

echo "✅ Proyecto, dependencias y caché eliminados."
echo "👉 Ahora puedes volver a clonar tu repo o subir tu código limpio."

