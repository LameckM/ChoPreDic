# Cholera Early-Warning System (Zambia)

Build order. Each step has a check before moving on.

1. Inspect data:  python -m ml.inspect_data data/raw/cholera.csv --date <col> --area <col> --cases <col>
2. Edit backend/config.py so the column names match your file
3. Prepare:       python -m ml.prepare
4. Train/compare: python -m ml.train
5. API:            uvicorn app.main:app --reload   (docs at http://127.0.0.1:8000/docs, check: python tests_api.py)
6. (next) React dashboard

Run everything from the backend folder. Data in backend/data/raw/cholera.csv.
tools/make_synthetic_data.py makes FAKE data for testing only.
