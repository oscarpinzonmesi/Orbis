Write-Host "⚠️ Borrando proyecto y entornos virtuales..."

# Ruta de tu proyecto
$projectPath = "C:\Users\oscar\Desktop\Orbis"

# Eliminar todo el contenido del proyecto (excepto el script mismo)
Get-ChildItem -Path $projectPath -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Eliminar entornos virtuales
Remove-Item -Recurse -Force "$projectPath\.venv" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$projectPath\venv" -ErrorAction SilentlyContinue

# Eliminar cachés de Python
Get-ChildItem -Path $projectPath -Recurse -Include "__pycache__","*.pyc" -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Vaciar caché de pip
pip cache purge

Write-Host "✅ Proyecto, dependencias y caché eliminados."
Write-Host "👉 Ahora puedes volver a clonar tu repo o subir tu código limpio."
