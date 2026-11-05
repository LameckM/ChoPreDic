# ChoPreDic React Dashboard

React + Vite dashboard for the Cholera Early-Warning System (Zambia).

## Requirements

- Node.js 18+
- The FastAPI backend running from the `backend` directory
- Trained model artifacts and processed data required by the backend

## Run locally

Terminal 1 — backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Terminal 2 — dashboard:

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173.

The dashboard uses `http://127.0.0.1:8000` by default. To change it, copy
`.env.example` to `.env` and set `VITE_API_BASE_URL`.

## API endpoints used

- `GET /health`
- `GET /api/summary`
- `GET /api/risk`
- `GET /api/alerts?min_level=medium`
- `GET /api/trends/national`
- `GET /api/districts`
- `GET /api/districts/{name}`
- `GET /api/model`

## Important data note

The current API dataset covers 2008–2018 and forecasts the next period from
that historical data. The dashboard displays the source and forecast years and
warns when the forecast period is historical. Risk scores are relative model
scores, not calibrated probabilities or operational outbreak declarations.

The API currently provides district names and IDs, but no district polygon
geometry. The dashboard therefore shows district risk rankings rather than
inventing a choropleth map. A map can be added once validated district boundary
GeoJSON is connected to the backend.
