# Cholera Prediction

**A Machine Learning-Based Cholera Outbreak Prediction and Early-Warning System for Zambia**

Cholera Prediction is a data-driven decision-support system designed to analyse historical cholera records across Zambian districts, estimate future outbreak risk, and present district-level predictions through an interactive dashboard.

The system combines machine learning, a REST API, historical district data, and geographical visualisation to make the results easier to interpret.

> **Important:** This is a research and decision-support system. It is not a medical diagnostic tool, does not guarantee that an outbreak will occur, and should not replace official public-health surveillance.

---

## 1. Project Objectives

- Analyse historical cholera cases across Zambian districts.
- Identify patterns associated with cholera outbreaks.
- Train and compare machine learning classification models.
- Estimate future outbreak risk at district level.
- Present predictions through a central dashboard.
- Support interpretation through historical trends, district assessments, and geographical risk visualisation.

## 2. Key Features

### Machine Learning
- Logistic Regression and Random Forest model comparison.
- Historical data preparation and feature engineering.
- Rolling-origin model evaluation.
- Automatic selection of the better-performing model based on Precision-Recall AUC.
- District-level risk scoring and classification.

### Backend API
- FastAPI-based REST API.
- Model loading and prediction processing.
- National summary statistics.
- District-level risk assessments.
- Historical district case records.
- National cholera trends.
- Early-warning alerts.
- Model evaluation information.

### Interactive Dashboard
- National overview and summary statistics.
- National cholera trends visualisation.
- District risk assessment table.
- Interactive geographical district risk map.
- District search and risk-level filtering.
- District-specific historical assessment modal.
- CSV export of district risk results.
- Early-warning list.
- Model comparison and feature importance information.
- Responsive desktop and mobile layout.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Machine learning | Scikit-learn |
| Data processing | Pandas, NumPy |
| Backend framework | FastAPI |
| API server | Uvicorn |
| Model persistence | Joblib |
| Frontend | React 18 |
| Frontend tooling | Vite |
| Charts | Recharts |
| Geographical mapping | Leaflet, React-Leaflet |
| Map data format | GeoJSON |

## 4. Machine Learning Approach

The system uses **supervised machine learning**, specifically binary classification.

The models are trained using historical district-level cholera records and relevant district characteristics.

### Models evaluated

**Logistic Regression**

A statistical classification algorithm used to estimate the likelihood of an outbreak class based on the input features.

**Random Forest**

An ensemble learning algorithm that combines multiple decision trees to produce a classification and risk score.

### Model evaluation

The system compares the models using a rolling-origin evaluation approach. This tests predictions across historical periods while ensuring that training data precedes the period being evaluated.

Evaluation metrics include:

- Precision
- Recall
- F1-score
- ROC AUC
- Precision-Recall AUC

The selected model is saved for use by the backend API.

### Risk classification

Predicted scores are grouped into three categories:

| Risk level | Classification |
|---|---|
| Low | Below 0.45 |
| Medium | 0.45 to below 0.65 |
| High | 0.65 and above |

**Interpretation:** These scores are relative model risk scores, not calibrated probabilities. A score of 0.70 does not mean there is a verified 70% chance of an outbreak.

## 5. Dataset

The project uses historical cholera and district-level information for Zambia.

The current historical dataset contains:

- 72 districts.
- Annual cholera records from 2008 to 2018.
- District population and demographic information.
- Water access and sanitation indicators.
- Poverty indicators.
- Distance to water bodies.

The current model forecast period is **2019**, based on the available historical data through 2018.

### Geographical data

The dashboard uses a historical Zambia district boundary GeoJSON dataset from 2017. All 72 districts in the case data match a boundary polygon.

The geographical boundaries are used to display existing district-level model classifications. They do not generate new predictions or change the underlying historical dataset.

## 6. System Architecture

The system consists of three main components:

1. **Data and machine learning layer:** Prepares historical data, trains classification models, evaluates performance, and produces the selected model artifact.
2. **Backend API:** Loads the selected model and historical data, processes predictions, and exposes the results through REST endpoints.
3. **Frontend dashboard:** Retrieves API data and presents national statistics, trends, district assessments, alerts, model information, and the geographical risk map.

```text
Historical Cholera Dataset
          |
          v
Data Preparation
          |
          v
Feature Engineering
          |
          v
Model Training & Evaluation
          |
          v
Selected ML Model
          |
          v
FastAPI Backend
          |
          v
React Dashboard
          |
          +---- National Overview
          +---- Cholera Trends
          +---- District Risk Table
          +---- Geographical Risk Map
          +---- Early-Warning Alerts
          +---- Model Evaluation
```

## 7. Project Structure

```text
ChoPreDic/
│
├── backend/
│   ├── app/
│   │   └── main.py
│   │
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   │
│   ├── ml/
│   │   ├── inspect_data.py
│   │   ├── reshape_wide.py
│   │   ├── prepare.py
│   │   └── train.py
│   │
│   ├── models/
│   │   ├── best_model.joblib
│   │   └── metrics.json
│   │
│   ├── config.py
│   ├── requirements.txt
│   └── tests_api.py
│
├── dashboard/
│   ├── public/
│   │   └── data/
│   │       └── zambia_districts_2017.geojson
│   │
│   ├── src/
│   │   ├── App.jsx
│   │   ├── DistrictRiskMap.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   │
│   ├── package.json
│   └── .env.example
│
├── .gitignore
└── README.md
```

## 8. Installation and Setup

### Prerequisites

Install the following before running the project:

- Python 3.11 recommended.
- Node.js 18 or later.
- npm.
- Git.

### Step 1: Clone the repository

```bash
git clone https://github.com/LameckM/ChoPreDic.git
cd ChoPreDic
```

### Step 2: Set up the backend

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Start the backend API

From inside the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Step 4: Set up the dashboard

Open a second terminal and navigate to the dashboard directory:

```bash
cd dashboard
```

Install frontend dependencies:

```bash
npm install
```

Configure the backend address if necessary by copying `.env.example` to `.env` and editing:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Open the dashboard at:

```text
http://localhost:5173
```

### Running on a local network

To open the dashboard from another device on the same network (for example a phone), use the computer's local IP address, here shown as `192.168.1.20`:

1. Start the backend with that dashboard origin allowed:

   ```bash
   CORS_EXTRA_ORIGINS=http://192.168.1.20:5173 uvicorn app.main:app --reload --host 0.0.0.0
   ```

   On Windows PowerShell:

   ```powershell
   $env:CORS_EXTRA_ORIGINS="http://192.168.1.20:5173"; uvicorn app.main:app --reload --host 0.0.0.0
   ```

2. In `dashboard/.env`, set `VITE_API_BASE_URL=http://192.168.1.20:8000`, then run `npm run dev`.
3. Open `http://192.168.1.20:5173` on the other device.

`dashboard/.env` is ignored by Git, so your own network address is never committed. The backend and dashboard must both be running.

## 9. Machine Learning Pipeline

The model training pipeline can be executed from the `backend` directory.

Prepare the historical data:

```bash
python -m ml.reshape_wide
```

Prepare the model dataset:

```bash
python -m ml.prepare
```

Train and compare the models:

```bash
python -m ml.train
```

The selected model and evaluation results are saved in:

```text
backend/models/
```

The existing trained model artifacts are included in the repository, so retraining is not required just to start the API when all required processed data files are present.

## 10. API Endpoints

The backend exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks API availability. |
| GET | `/api/summary` | Returns national summary statistics. |
| GET | `/api/risk` | Returns district-level forecast risk scores. |
| GET | `/api/alerts?min_level=medium` | Returns medium- and high-risk districts. |
| GET | `/api/trends/national` | Returns national historical cholera trends. |
| GET | `/api/districts` | Returns district information. |
| GET | `/api/districts/{name}` | Returns an individual district assessment and history. |
| GET | `/api/model` | Returns model evaluation and feature importance information. |

## 11. Testing

Backend API tests can be run from the `backend` directory:

```bash
python tests_api.py
```

The dashboard can be checked using the production build command from the `dashboard` directory:

```bash
npm run build
```

The application should also be tested through the browser to verify API connectivity, charts, district filtering, map interactions, district details, alerts, and CSV export.

## 12. Limitations

- The historical dataset currently covers 2008–2018.
- The current forecast period is 2019 and should not be interpreted as a live 2026 outbreak forecast.
- Model performance depends on the quality, completeness, and representativeness of the available historical data.
- Risk scores are relative model scores, not calibrated outbreak probabilities. The dashboard shows them as a score out of 100 for this reason.
- The data is annual, so the system ranks districts by risk for the next year. It is not a weeks-ahead early-warning signal. Monthly or weekly surveillance data would be needed for that.
- Historical district boundaries may not represent later administrative boundary changes.
- Geographical classification displays existing model results; it does not independently verify outbreaks.
- The system is intended for research and decision support, not clinical diagnosis or official outbreak confirmation.

## 13. Future Improvements

Potential future work includes:

- Validation of all district-to-boundary matches.
- Integration of newer verified cholera surveillance data.
- Evaluation using more recent independent data.
- Further model validation and calibration.
- Improved alert delivery and reporting workflows.
- Deployment of the backend and dashboard to a publicly accessible server.

## 14. Project Status

The backend API, machine learning pipeline, and React dashboard have been developed. The dashboard includes national statistics, historical trends, district-level risk assessments, an interactive geographical risk map, early-warning alerts, and model evaluation information.

System integration and final testing remain important before deployment or operational use.

---

**Project:** Cholera Prediction  
**Repository:** [LameckM/ChoPreDic](https://github.com/LameckM/ChoPreDic)  
**Purpose:** District-level cholera outbreak prediction and early-warning decision support in Zambia.
