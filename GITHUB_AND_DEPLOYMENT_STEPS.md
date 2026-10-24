# Finish the submission — do these steps in order

## 1. Create GitHub repository
1. Sign in to GitHub and create a **public** repository named `GeoPilot-AI`.
2. Do not add a separate README/license from GitHub if you are uploading this folder's README (to avoid conflicts).
3. Upload all files in this folder, including `main.py`, `app.py`, `requirements.txt`, `.gitignore`, `README.md`, `Procfile`, `render.yaml`, and the disclosure/example documents.
4. Check that the public repository opens in a private/incognito browser window.

## 2. Deploy API
1. Sign in to Render and create a Web Service from the GitHub repository.
2. Runtime: Python. Build command: `pip install -r requirements.txt`.
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Health check path: `/health`.
5. Deploy and copy the exact service URL Render gives you.
6. Test `https://YOUR-SERVICE-URL/health` in a browser. It must return JSON.
7. Send a POST to `/recommend` using the request example. Confirm it returns a recommendation, not HTTP 502/500. Test again after a short wait to check cold-start behavior.

## 3. Model caveat
The code uses Ollama at a configurable URL, defaulting to localhost. Render will not have access to Ollama on your personal PC. API functionality can still return a fallback explanation, but this is not the same as running the LLM on the public host. If the judges require the model to be served live by the endpoint, this must be solved before submission.

## 4. UI (optional)
The form requires a public API endpoint; the UI is optional unless the rules require it. If deploying Streamlit, set `GEOPILOT_API_URL` to the API service's base URL, such as `https://YOUR-SERVICE-URL` (no trailing `/recommend`).

## 5. Final checks
- Open repository and `/health` in a private browser.
- Run the POST request against the public endpoint.
- Confirm exact public model card URL and that the event accepts using the upstream base model without custom fine-tuning.
- Enter the exact request method, public URL, and JSON body.
- Do not claim OSM/venue/road/traffic/green-cover analysis.
- Keep the API service available for the judging window. Free-tier sleep/cold starts can be a risk.
