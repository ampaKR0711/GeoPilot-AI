# API request example

**Local development example only — not suitable as the final public endpoint URL.**

Method: `POST`

URL:
```text
http://127.0.0.1:8000/recommend
```

Request body:
```json
{
  "activity": "jogging",
  "location": "Bhubaneswar, Odisha, India",
  "radius_km": 5,
  "time_range": "tomorrow morning",
  "age": 22,
  "constraints": [
    "sensitive to air pollution"
  ]
}
```

cURL:
```bash
curl -X POST "http://127.0.0.1:8000/recommend" \
  -H "Content-Type: application/json" \
  -H "accept: application/json" \
  -d '{
    "activity": "jogging",
    "location": "Bhubaneswar, Odisha, India",
    "radius_km": 5,
    "time_range": "tomorrow morning",
    "age": 22,
    "constraints": ["sensitive to air pollution"]
  }'
```

**Before submission:** replace `http://127.0.0.1:8000/recommend` with the actual verified public API URL. Do not submit a localhost URL.
