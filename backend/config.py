"""
Single place to describe YOUR data. Edit this file, nothing else, when your
column names or file name differ.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"

# ---- Your raw data ---------------------------------------------------------
# The file as you have it: one row per district, one column per year.
RAW_WIDE_FILE = RAW_DIR / "cholera_wide.csv"
WIDE_YEAR_REGEX = r"y\d{4}"          # matches y2008, y2009, ...
# The reshaped file (one row per district per year) that the pipeline reads.
DATA_FILE = RAW_DIR / "cholera_long.csv"

DATE_COL = "year"
AREA_COL = "District"
CASES_COL = "cases"

# "Y" = one row per district per year, "M" = one row per district per month.
FREQ = "Y"
PANDAS_FREQ = {"Y": "YS", "M": "MS"}[FREQ]
PERIOD = FREQ

# Static predictors from your file. Dist_ID, rural_popl and urban_popl are left
# out: the first is an ID, the other two are just pop2010 split by urban(%).
COVARIATES = ["pop2010", "urban(%)", "water(%)", "sanitation(%)", "poverty(%)",
              "Dist_Waterbody (km)"]
LOG_COVARIATES = ["pop2010"]          # heavy-tailed, so we use log(1 + x)

# ---- How the prediction target is defined ---------------------------------
# "Outbreak" = a district-year with more than OUTBREAK_THRESHOLD cases.
OUTBREAK_THRESHOLD = 0
# We predict whether the district has an outbreak HORIZON periods (years) ahead.
HORIZON = 1
LAGS = [1, 2]

FILL_MISSING_CASES_WITH_ZERO = False

# ---- Evaluation ------------------------------------------------------------
# Rolling-origin test: for each of the last N periods, train only on the past
# and predict that period. With only ~10 years of data this is far more
# trustworthy than one train/test cut.
N_TEST_PERIODS = 5
MIN_TRAIN_PERIODS = 3
RANDOM_STATE = 42

# ---- Alert levels (used by the API) ----------------------------------------
# These are model RISK SCORES between 0 and 1, not calibrated probabilities:
# the models are trained with class weights so outbreaks are not ignored, which
# pushes scores up. Read them as "higher = riskier", not "40% chance".
RISK_MEDIUM = 0.45
RISK_HIGH = 0.65
