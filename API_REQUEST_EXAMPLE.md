# Exact API request example

**Method:** `POST`

**Full URL:** `https://YOUR-ACTUAL-PUBLIC-API-HOST/recommend`

Replace the host placeholder only after deployment; do not submit localhost or `127.0.0.1`.

**JSON body:**
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

**PowerShell test after deployment:**
```powershell
$body = @{
  activity = "jogging"
  location = "Bhubaneswar, Odisha, India"
  radius_km = 5
  time_range = "tomorrow morning"
  age = 22
  constraints = @("sensitive to air pollution")
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "https://YOUR-ACTUAL-PUBLIC-API-HOST/recommend" `
  -ContentType "application/json" -Body $body
```
