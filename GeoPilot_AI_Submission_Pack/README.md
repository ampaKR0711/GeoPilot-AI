# GeoPilot AI — GeoAI Hackathon Submission

GeoPilot AI is an AI-assisted outdoor activity planning prototype. It evaluates hourly weather and air-quality indicators and produces a risk-aware recommendation for a requested activity and location.

## Current implementation
- FastAPI backend (`main.py`) with `/health` and `/recommend` endpoints.
- Streamlit interface (`app.py`).
- Local Qwen2.5-1.5B model through Ollama for evidence-grounded explanations, with a fallback explanation path.
- Open-Meteo geocoding, forecast, and air-quality APIs.
- Prototype heuristic scoring and pollution-risk advisories.

## Important status disclosure
This is a prototype, not a validated safety or medical product. Nearby places/POIs, roads, traffic, green cover, water bodies, and industrial proximity are **not implemented** in the current API version. The project has not yet been deployed to a verified public API endpoint. A recent live test encountered DNS resolution failure reaching Open-Meteo; test network connectivity again before judging.

## Run locally (Windows)
From the project folder:
```cmd
.venv\Scripts\activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
In a second terminal:
```cmd
cd /d C:\Users\KIIT0001\GeoPilot_AI
.venv\Scripts\activate
python -m streamlit run app.py
```
- API health: http://127.0.0.1:8000/health
- Swagger docs: http://127.0.0.1:8000/docs
- Streamlit UI: http://localhost:8501

Ollama must be installed and running with `qwen2.5:1.5b` available:
```cmd
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b "Reply with exactly: model test successful"
```

## Dependencies
Install the packages in `requirements.txt` in your virtual environment. The existing local environment may have additional packages; validate from a clean environment before claiming reproducibility.

## API request example
See `api_request_example.md`. The endpoint URL shown there is LOCAL ONLY. Replace it with the verified public URL before submitting to the hackathon form.

## Data-source disclosure
- Open-Meteo Geocoding API — location lookup.
- Open-Meteo Forecast API — hourly weather variables.
- Open-Meteo Air Quality API — hourly US AQI and PM2.5 when available.
- Qwen2.5-1.5B-Instruct — local open-weight language model via Ollama.

## Submission checklist
- [ ] Add the actual project source files (`main.py`, `app.py`) to the repository.
- [ ] Make the repository public or grant the organizers access.
- [ ] Verify the Hugging Face model link and license meet the form's model-link requirement. The upstream model page is not a custom team-trained model/adapter.
- [ ] Deploy the API or expose it through a stable public URL.
- [ ] Test the public endpoint from a different network/device.
- [ ] Ensure the endpoint remains reachable for the full judging window (25–26 October).
- [ ] Upload the included 5-slide presentation PDF.
- [ ] Do not tick the final confirmation until each statement is true.
