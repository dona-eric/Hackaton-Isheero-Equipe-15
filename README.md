# 🇧🇯 Bénin HACKATONiSHEERO × DataCamp 2026

Bienvenue dans le dépôt du projet **HACKATON ISHEERO EQUIPE 15** ! Ce projet est dédié à la surveillance, l'extraction et l'analyse avancée des événements liés au **Bénin** couverts par la base de données mondiale GDELT (01 Janvier 2025 – 01 Janvier 2026).

### Objectifs:

1- Analyse l'image du Bénin à l'échelle internationale à travers les médias sociaux

2- Détecter les tendances et anomalies dans la couverture médiatique du Bénin

3- Développer un modèle de prédiction pour anticiper les crises potentielles

Les membres de l'équipe sont :

* 

L'originalité de ce travail réside dans le dépassement d'une modélisation binaire pour adopter une approche de **clustering non supervisée**, permettant de cartographier finement l'image du pays à l'échelle internationale et sa viralité sur les médias sociaux.

---

## 🏗️ Architecture du Pipeline ETL

Le pipeline est conçu pour être robuste, modulaire et optimisé pour la mémoire (`src/pipeline/`) :

1.  **Collector (`collector.py`)** : Extraction via **BigQuery** (recommandé pour le volume) ou via téléchargement direct des fichiers ZIP GDELT optimisé pour la RAM.
2.  **Cleaner (`cleaner.py`)** : 
    * Optimisation des types (Nullable types) pour réduire l'empreinte mémoire.
    * Enrichissement temporel et imputation intelligente de la tonalité (`AvgTone`).
    * Conversion des codes CAMEO en labels explicites.
3.  **Loader (`loader.py`)** : Chargement et export haute performance au format **Parquet compressé (zstd)**.

---

## 📊 Analyse de l'Image Pays & Clustering

Plutôt qu'une simple classification, nous avons implémenté des algorithmes de clustering pour découvrir les patterns cachés dans l'image médiatique du Bénin.

### Méthodologie
* **Algorithmes testés** : DBSCAN (détection d'anomalies), Spectral Clustering (relations complexes) et **GMM (Gaussian Mixture Model)**.
* **Optimisation** : Le nombre de clusters a été déterminé par le calcul du **score BIC** (Bayesian Information Criterion), révélant un optimum à **k=5**.
* **Features prioritaires** : `GoldsteinScale` (impact), `AvgTone` (sentiment), `NumMentions` (viralité) et `MentionDocTone` (sensibilité).

### Insights Clés
* **C1 - Zone de Risque** : Événements à fort impact négatif et sentiment dégradé, captant une large part de la viralité.
* **C4 - Sensibilité Sociale** : Identifie les sujets à forte viralité sur les réseaux sociaux avant qu'ils ne deviennent des crises majeures.
* **Viralité** : Les événements négatifs se propagent en moyenne **3 fois plus vite** que les nouvelles de coopération positive.

---

## 🚀 Reproductibilité & Modèle Hugging Face

Le modèle v1 est versionné et hébergé sur **Hugging Face** pour une utilisation immédiate.

### 1. Installation
```bash
git clone [https://github.com/dona-eric/Hackaton-Isheero-Equipe-15.git](https://github.com/dona-eric/Hackaton-Isheero-Equipe-15.git)
cd Hackaton-Isheero-Equipe-15
pip install -r requirements.txt



### 2. COnfiguration

```bash

export HF_TOKEN=''

```

### 3. telechargement du modele

```bash

import joblib
from huggingface_hub import hf_hub_download

# Téléchargement du modèle GMM optimisé
model_path = hf_hub_download(
    repo_id="donerick/gaussian-model-v1",
    filename="gaussian-model.pkl",
    token="VOTRE_TOKEN_HF"
)

# Chargement
model = joblib.load(model_path)
print("Modèle GMM chargé avec succès.")

```
### 4. Pipeline de collecte et de nettoyage

```bash

# Lancement du pipeline
python src/pipeline/run_pipeline.py \
  --start-date 2025-01-01 \
  --end-date 2026-01-01 \
  --mode "both" \
  --process "all"

```