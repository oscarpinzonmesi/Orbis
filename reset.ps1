# reset.ps1 - limpia todo el proyecto Orbis

Write-Host "=== Limpiando el proyecto Orbis... ==="

# Elimina la carpeta del entorno virtual si existe
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force ".venv"
    Write-Host "[OK] .venv eliminado"
}

# Elimina cachés de Python
Get-ChildItem -Recurse -Include "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Cachés de Python eliminados"

# Elimina carpeta dist/build (si existe)
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Write-Host "[OK] Archivos de compilación eliminados"

Write-Host "=== Proyecto limpio. Listo para reinstalar dependencias. ==="
