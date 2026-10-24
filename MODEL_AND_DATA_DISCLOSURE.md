# Model and data disclosure

## Model
- Name: Qwen2.5-1.5B-Instruct
- Runtime used in local prototype: Ollama (`qwen2.5:1.5b`)
- Upstream model card: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
- The code sends structured forecast evidence to the model for a short explanation. The numeric ranking is calculated by Python heuristics, not by the LLM.
- No custom weights or fine-tuned adapter are included in this project package.
- Cloud deployment does not automatically include the local Ollama model; unless a reachable Ollama endpoint is configured, the API uses a fallback explanation.

## APIs
- Open-Meteo Geocoding API: location name to coordinates.
- Open-Meteo Forecast API: hourly temperature, precipitation, wind and weather code.
- Open-Meteo Air Quality API: hourly US AQI and PM2.5 when available.
- OpenStreetMap/OSM features are not integrated in this version.

## Honest scope
The radius field is accepted but is not used to search nearby places. Roads, traffic, green cover, water bodies and industrial proximity are not evaluated. Results are not medical advice or a guarantee of safety.
