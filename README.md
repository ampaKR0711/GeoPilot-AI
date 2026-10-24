# GeoPilot AI — GeoAI Hackathon Prototype

GeoPilot AI helps users compare forecast hours for outdoor activities using a requested location, activity, time window, and optional preferences. It combines hourly weather and (when available) air-quality forecast data with transparent prototype scoring, then uses a locally hosted Qwen2.5 1.5B model for a concise explanation when that model is reachable.

## Current capabilities
- Location lookup using the Open-Meteo Geocoding API.
- Hourly weather forecast comparison using the Open-Meteo Forecast API.
- Optional hourly US AQI and PM2.5 from the Open-Meteo Air Quality API.
- Heuristic ranking with reasons, risks, and pollution cautions.
- Optional Qwen2.5 1.5B explanation through Ollama; deterministic fallback explanation if unavailable.
- Streamlit interface and FastAPI backend.

## Known limitations — please disclose honestly
- The radius is accepted as a preference but nearby venues are not searched.
- Roads, traffic, vegetation/green cover, water bodies, and industrial proximity are not analyzed.
- The scoring is a prototype heuristic, not validated medical or safety advice.
- Air-quality values may be unavailable. A missing value is uncertainty, not evidence of clean air.
- On a cloud host, the local Ollama model is not automatically available. The API falls back to a rule-based explanation unless `OLLAMA_URL` points to a reachable Ollama service.
- The external Open-Meteo services must be reachable from the deployed host and from the user's network.

## Run locally (Windows PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start Ollama separately if you want the local model explanation:
```powershell
ollama pull qwen2.5:1.5b
ollama serve
```
If Ollama is already running as a Windows service, do not start a second server.

Terminal 1 — API:
```powershell
uvicorn main:app --host 127.0.0.1 --port 8000
```
API docs: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

Terminal 2 — UI:
```powershell
$env:GEOPILOT_API_URL = "http://127.0.0.1:8000"
streamlit run app.py
```

## API request example
`POST /recommend` with JSON:
```json
{
  "activity": "jogging",
  "location": "Bhubaneswar, Odisha, India",
  "radius_km": 5,
  "time_range": "tomorrow morning",
  "age": 22,
  "constraints": ["sensitive to air pollution"]
}
```
Use the full public URL after deployment, for example `https://YOUR-API-SERVICE.onrender.com/recommend` only after replacing the placeholder with your actual deployed URL.

## Deploy the API on Render
1. Create a GitHub repository and push this project.
2. In Render, create a new **Web Service** from that repository.
3. Use build command `pip install -r requirements.txt`.
4. Use start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Set health-check path to `/health`.
6. Once deployed, test `https://YOUR-ACTUAL-SERVICE.onrender.com/health` and then make a POST request to `/recommend`.
7. If the free service sleeps, the first request can be slow. Keep the service and the required model/data source reachable throughout judging.

## Deploy the Streamlit UI separately (optional)
Deploy the same repository as a Streamlit app and set the environment variable `GEOPILOT_API_URL` to the actual public API base URL (without `/recommend`). If you only need the API endpoint for the form, the Streamlit UI is optional.

## Model disclosure
- Base model used locally: `Qwen2.5-1.5B-Instruct` via Ollama tag `qwen2.5:1.5b`.
- Hugging Face model card: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
- This repository does not contain custom-trained weights or a fine-tuned adapter. Do not describe the upstream base model as a custom model created by the team.
- Verify the hackathon's exact model-license and submission rules before submitting.

## Data sources
- Open-Meteo Geocoding API: https://geocoding-api.open-meteo.com/
- Open-Meteo Forecast API: https://open-meteo.com/
- Open-Meteo Air Quality API: https://open-meteo.com/en/docs/air-quality-api

## Safety and accuracy
The displayed score is a prototype ranking, not a safety rating. Forecasts can change. Users should check official local advisories and use caution, especially when air-quality data is missing or elevated.
