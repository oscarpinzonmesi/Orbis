# Orbis

**Orbis** es un servicio de agenda y recordatorios que funciona como una **libreta invisible** en la nube.  
Guarda, busca, borra y reprograma citas usando un archivo `agenda.json`.

👉 Orbis no interactúa directamente con usuarios finales.  
👉 Se comunica a través de una API REST que entiende comandos simples (`/agenda`, `/registrar`, etc.).  
👉 El asistente **MesaGPT** es quien traduce tus frases naturales en comandos y se conecta con Orbis.

---

## Endpoints principales

- `GET /` → Prueba rápida (muestra "✅ Orbis API funcionando en Render").
- `POST /procesar`  
  - Body JSON:  
    ```json
    { "texto": "/agenda", "modo": "json" }
    ```  
  - Respuesta: estado de la agenda.
- `GET /proximos` → Devuelve los eventos próximos en la siguiente ventana de tiempo.

---

## Requisitos

- Python 3.10+
- Flask
- gunicorn
- requests
- python-telegram-bot (para el bot de MesaGPT)
- openai

---

## Despliegue en Render

1. `runtime.txt` → define la versión de Python.  
2. `requirements.txt` → dependencias.  
3. `Procfile` → indica el punto de entrada (`python telegram_mesagpt.py`).  

---

## Estructura recomendada

