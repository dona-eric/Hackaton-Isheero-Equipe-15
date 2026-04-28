# config.py — Configuration centrale du projet
# Bénin Insights Challenge 

from pathlib import Path
from datetime import datetime, timedelta
import logging
import os
from logging.handlers import RotatingFileHandler
# Racine du projet 
ROOT_DIR = Path(__file__).resolve().parent

# Répertoires de données
DATA_DIR       = ROOT_DIR / "data"
RAW_DIR        = DATA_DIR / "raw"
PROCESSED_DIR  = DATA_DIR / "processed"
EXPORTS_DIR    = DATA_DIR / "exports"
MODELS_DIR     = ROOT_DIR / "models" / "saved"

# create the dir if not exist
for dir in [RAW_DIR, PROCESSED_DIR, EXPORTS_DIR, MODELS_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

# settings GDELT
# Code FIPS 10-4 du Bénin
BENIN_COUNTRY_CODE = "BN"
BENIN_ADM1_PREFIX  = "BN"          # Préfixe des codes admin. niveau 1

# Fenêtre temporelle : 12 derniers mois
END_DATE   = datetime.today()
START_DATE = END_DATE - timedelta(days=365)

DATE_FORMAT = "%Y%m%d"

# urls GDELT
GDELT_BASE_URL        = "http://data.gdeltproject.org/events"
GDELT_V2_BASE_URL     = "http://data.gdeltproject.org/gdeltv2"
GDELT_MASTER_LIST_URL = f"{GDELT_V2_BASE_URL}/masterfilelist.txt"
GDELT_LAST_15_URL     = f"{GDELT_V2_BASE_URL}/lastupdate.txt"

# Google BigQuery
BQ_PROJECT     = "isheero-gcp-project-id"    #id project
BQ_DATASET     = "gdelt-bq.gdeltv2"
BQ_TABLE       = "events"
BQ_QUOTA_TB    = 1.0                        # Quota gratuit mensuel (To)

# Colonnes GDELT (58 champs, GDELT 2.0)
GDELT_COLUMNS = [
    "GlobalEventID", "Day", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
    "QuadClass", "GoldsteinScale", "NumMentions", "NumSources",
    "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_Fullname", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long",
    "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_Fullname", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long",
    "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_Fullname", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long",
    "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

# Les Types de données
GDELT_DTYPES = {
    "GlobalEventID":      "int64",
    "Day":                "int32",
    "MonthYear":          "int32",
    "Year":               "int16",
    "FractionDate":       "float32",
    "IsRootEvent":        "int8",
    "QuadClass":          "int8",
    "GoldsteinScale":     "float32",
    "NumMentions":        "int16",
    "NumSources":         "int16",
    "NumArticles":        "int16",
    "AvgTone":            "float32",
    "Actor1Geo_Type":     "int8",
    "Actor1Geo_Lat":      "float32",
    "Actor1Geo_Long":     "float32",
    "Actor2Geo_Type":     "int8",
    "Actor2Geo_Lat":      "float32",
    "Actor2Geo_Long":     "float32",
    "ActionGeo_Type":     "int8",
    "ActionGeo_Lat":      "float32",
    "ActionGeo_Long":     "float32",
    "DATEADDED":          "int64",
}

# Codes CAMEO QuadClass
QUAD_CLASS_LABELS = {
    1: "Coopération verbale",
    2: "Coopération matérielle",
    3: "Conflit verbal",
    4: "Conflit matériel",
}

#  Logging


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str = "logs_dev") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # éviter duplication des logs
    if logger.hasHandlers():
        return logger

    # Format des logs
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    #  Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler avec rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ajouter handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
if __name__ == "__main__":
    setup_logger()
    logging.debug(f"=============Logging HACKATON ISHEERO GDELT===========")