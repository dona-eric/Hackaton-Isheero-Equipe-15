import os
import pathlib
import sys
from dotenv import load_dotenv
from huggingface_hub import HfApi, hf_hub_download
import joblib

# Gestion du path pour l'import local
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import setup_logger

logger = setup_logger(name="HF_Upload_Load")
load_dotenv()

# Configuration
TOKEN_HF = os.getenv("token_hf")
REPO_NAME = "gaussian-model-v1"
USERNAME = "donerick"
REPO_ID = f"{USERNAME}/{REPO_NAME}"
FILE_PATH = "models/best_gmm_model.pkl"

api = HfApi(token=TOKEN_HF) # On lie le token à l'instance API dès le début

## 1. Création du dépôt
try:
    api.create_repo(
        repo_id=REPO_ID,
        repo_type="model",
        private=False,
        exist_ok=True # Évite de gérer l'erreur manuellement si le dépôt existe déjà
    )
    logger.info(f"Dépôt {REPO_ID} prêt.")
except Exception as e:
    logger.error(f"Erreur lors de la création du dépôt : {e}")

## 2. Upload du fichier
try:
    api.upload_file(
        path_or_fileobj=FILE_PATH,
        path_in_repo="gaussian-model.pkl",
        repo_id=REPO_ID
    )
    logger.info(f"Modèle uploadé avec succès sur {REPO_ID}")
except Exception as e:
    logger.error(f"Erreur lors de l'upload : {e}")

## 3. Téléchargement et test de chargement
try:
    model_path = hf_hub_download(
        repo_id=REPO_ID,
        filename="gaussian-model.pkl",
        token=TOKEN_HF
    )
    model = joblib.load(model_path)
    logger.info("Modèle rechargé depuis HF avec succès.")
except Exception as e:
    logger.error(f"Erreur lors du rechargement : {e}")