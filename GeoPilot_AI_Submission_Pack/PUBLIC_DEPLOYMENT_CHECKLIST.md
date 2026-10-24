# Public endpoint — urgent deployment checklist

The judges require a public HTTP endpoint and an example request. `127.0.0.1` and `localhost` are only reachable on your own machine and are not acceptable as the final URL.

## Before choosing a deployment method
1. Confirm `http://127.0.0.1:8000/health` works locally.
2. Confirm Open-Meteo DNS/network access is working again. A recent request failed with `NameResolutionError` for `geocoding-api.open-meteo.com`.
3. Confirm Ollama's API works locally at `http://localhost:11434/api/generate`.
4. Choose a public hosting/tunnel approach that remains running throughout judging.

## Important Ollama constraint
The API calls Ollama at `http://localhost:11434`. If the backend is deployed to a cloud host, that URL points to the cloud host itself, not your laptop. The model integration will not work remotely unless Ollama is deployed alongside the API or the configuration is deliberately adapted to a securely reachable model service. Do not expose Ollama's port publicly without appropriate security.

## Temporary tunnel option
A tunnel can expose the API running on your laptop, but:
- your laptop, API process, internet connection, and Ollama must remain running;
- the tunnel URL may change after restarting unless you configure a stable named tunnel;
- test the public URL from mobile data or another network;
- the endpoint will not work if the laptop sleeps or network/DNS is unavailable.

After creating a verified public URL, the form's endpoint field should point to:
`https://YOUR-REAL-PUBLIC-HOST/recommend`

Do not use the placeholder above. Test `POST /recommend` against the real URL and ensure it returns a valid response before submission.
