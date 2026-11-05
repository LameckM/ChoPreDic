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

The map uses a 2017 district boundary file stored in
`public/data/zambia_districts_2017.geojson`. It only colours districts using the
risk levels returned by the API, so it displays existing model results and does
not generate new predictions. Boundaries may differ from later administrative
changes.

Risk scores are shown out of 100 because they are relative rankings, not
probabilities.

## Using another device on the network

`.env` is not committed to Git. Copy `.env.example` to `.env`, then set
`VITE_API_BASE_URL` to the computer's local IP address (for example
`http://192.168.1.20:8000`). Start the backend with
`CORS_EXTRA_ORIGINS=http://192.168.1.20:5173` so it accepts requests from the
dashboard origin.
