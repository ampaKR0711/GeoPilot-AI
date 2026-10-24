# Model and data disclosure

## Model
- Model used locally: `qwen2.5:1.5b` through Ollama.
- Suggested upstream model page to verify: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
- The upstream model is not a custom GeoPilot model or LoRA adapter trained by the team. Confirm that the organizers accept an upstream base-model link for the required Hugging Face field.
- The form requires an open-weights model at or below 3B parameters and asks for a public model/adapter link, model card, and open license. Verify all these conditions directly on the model card before confirming.

## Data sources / APIs
- Open-Meteo Geocoding API: https://geocoding-api.open-meteo.com/
- Open-Meteo Forecast API: https://open-meteo.com/
- Open-Meteo Air Quality API: https://open-meteo.com/en/docs/air-quality-api

The Air Quality API is optional in the implementation if it is unavailable. OpenStreetMap/Overpass features are not implemented in the current API version and should not be listed as used APIs unless the source code is updated to use them.

## Limitations
- Scores are heuristic and not validated medical or safety advice.
- External network/API access may fail; a DNS resolution failure occurred during testing.
- Nearby venues, road networks, traffic, vegetation, water bodies, and industrial proximity are not implemented in the current API version.
