# 🇧🇯 Bénin Insights Challenge — HACKATON iSHEERO × DataCamp 2026
> **Équipe 15** — Surveillance, analyse et modélisation de l'image internationale du Bénin via GDELT

---

## 📌 Vue d'ensemble

Ce projet analyse les **19 368 événements GDELT** impliquant le Bénin sur la période **01 janvier 2025 → 01 janvier 2026**, enrichis par **plus de 13 000 mentions médiatiques** issues de sources mondiales.

L'originalité de ce travail réside dans le **dépassement d'une modélisation binaire** pour adopter une approche de **clustering non supervisé** (DBSCAN, Spectral Clustering, GMM), permettant de cartographier finement l'image du pays à l'échelle internationale, sa viralité médiatique et ses zones de sensibilité.

---

## 👥 Équipe

| Rôle | Membre |
|---|---|
| Data Engineer | Peace Solange ADOKPO |
| Data Scientist | Mamadou  Diallo|
| ML Engineer | Eric KOULODJI |
| ML Engineer | Sunday KOGBETSE |

---

## 🎯 Objectifs

1. **Analyser l'image du Bénin** à l'échelle internationale à travers les médias mondiaux
2. **Détecter les tendances et anomalies** dans la couverture médiatique (ex : pic de décembre 2025)
3. **Cartographier les risques, viralités et sensibilités** via clustering non supervisé

---

## Note sur le code pays GDELT

> Le Bénin est identifié par le code **`BN`** dans le standard **FIPS 10-4** utilisé par GDELT.
> **Ne pas confondre avec `BC` (Botswana).**
> Le filtre SQL correct est : `ActionGeo_CountryCode = 'BN'`

---

## 📦 Sources de données

| Source | Description | Priorité | Statut |
|---|---|---|---|
| **Events** | Qui a fait quoi à qui, quand, où — 58 colonnes GDELT | ★★★ | Collecté |
| **Mentions** | Chaque article citant un événement (ton, délai, source) | ★★★ |  Collecté |
| **GKG** | Thèmes CAMEO, entités, citations, ton article complet | ★★★ | En cours |
| **N-grammes** | Fréquence des mots-clés (depuis jan. 2020) | ★★ | Phase 2 |
| **Graph datasets** | Réseaux d'acteurs et d'influence | ★★ | Phase 2 |

---

## 🔧 Pipeline ETL

### Étape 1 — Collecte de données

Charge le CSV exporté depuis BigQuery. Vérifie la présence des colonnes critiques et signale le bruit **BENIN CITY** (ville du Nigeria présente dans les données à ne pas confondre avec un acteur béninois).

### Étape 2 — Nettoyage des données

**17 colonnes sélectionnées** sur 61 disponibles. Les 44 exclues sont soit quasi-vides (< 5% remplies), soit redondantes, soit hors focus projet.

**Colonnes conservées :**
- `GLOBALEVENTID`, `SQLDATE` → identité et date
- `Actor1Name`, `Actor1CountryCode`, `Actor1Type1Code` → acteur initiateur
- `Actor2Name`, `Actor2CountryCode`, `Actor2Type1Code` → acteur cible
- `EventRootCode`, `QuadClass`, `IsRootEvent` → nature de l'événement
- `GoldsteinScale`, `AvgTone` → stabilité et ton GDELT
- `NumMentions`, `NumSources` → couverture quantitative
- `ActionGeo_FullName`, `ActionGeo_Lat`, `ActionGeo_Long` → géographie
- `SOURCEURL` → traçabilité journalistique

**Features dérivées créées :**
| Feature | Calcul | Usage |
|---|---|---|
| `date` | SQLDATE → datetime | Agrégations temporelles |
| `is_conflict` | QuadClass ∈ {3,4} | Clustering, filtrage |
| `is_cooperation` | QuadClass ∈ {1,2} | Clustering, filtrage |
| `QuadClass_label` | Map code → libellé FR | Lisibilité |
| `media_intensity` | Mentions + Sources×2 | Mesure de viralité |
| `tone_polarity` | AvgTone < -5 / -5..5 / > 5 | Segmentation ton |

### Étape 3: Chargement des données

Export en CSV (encodage `utf-8`) ou Excel pour les non-techniciens.

---

## 📊 Insights clés — Analyse exploratoire

### Sur les Events (19 368 événements)

| Indicateur | Valeur | Interprétation |
|---|---|---|
| % coopératifs | 73.6% | Dynamique diplomatique dominante |
| % conflictuels | 26.4% | dont 14% conflits matériels concrets |
| Goldstein moyen | +0.54 | Légèrement stabilisant |
| Tonalité médias | -1.59 | Image légèrement négative |
| Pic anomal | Déc. 2025 | 4 221 événements (x2.5 la moyenne) |

### Anomalie décembre 2025

Décembre 2025 concentre **4 221 événements** et **5 896 mentions** (x3.3 la moyenne mensuelle). Le Goldstein chute à +0.16 (quasi-neutre) et le ton à -2.65. Les sources nigérianes sont particulièrement actives ce mois. **L'événement déclencheur reste à investiguer.**

### Sur les Mentions (13 090 events enrichis)

| Indicateur | Valeur | Interprétation |
|---|---|---|
| Délai de propagation | 80% < 1h | Couverture quasi temps réel |
| Events viraux (> 5 mentions) | 225 (1.7%) | Longue traîne très marquée |
| Source la plus négative | New Republic (-9.0) | Couverture critique internationale |
| Source la plus positive | Forbes (+5.9) | Couverture économique favorable |
| Corrélation AvgTone ↔ Ton réel | R = 0.70 | GDELT légèrement optimiste |

### Acteurs clés identifiés

- **Forces armées non-étatiques (UAF)** : Goldstein moyen -6.04 → principal facteur déstabilisateur
- **Criminalité (CRM)** : Goldstein -2.93
- **Gouvernement** : Goldstein +1.02 → acteur stabilisant
- **Nigeria** : partenaire le plus actif (relation bilatérale dominante)
- **BENIN CITY** : ville du Nigeria apparaissant 778 fois → bruit à filtrer

---

## Modélisation — Clustering non supervisé

### Pourquoi le clustering plutôt que la classification ?

Une approche binaire (conflit/coopération) serait trop réductrice. Les données GDELT recèlent des **patterns complexes et multidimensionnels** — zones de risque, événements viraux, sensibilités géopolitiques — que seul un clustering non supervisé peut révéler sans a priori.

### Features prioritaires pour le clustering

Sélectionnées après analyse PCA (8 composantes capturent 90% de la variance) et étude des corrélations :

| Feature | Dimension mesurée | Source |
|---|---|---|
| `GoldsteinScale` | Stabilité politique | Events |
| `tone_doc_moyen` | Image réelle dans les médias | Mentions |
| `tone_doc_std` | Controverse / divergence entre médias | Mentions |
| `nb_mentions` | Viralité brute | Mentions |
| `doc_len_moyen` | Profondeur de la couverture | Mentions |
| `delai_moy_h` | Vitesse de propagation | Mentions |
| `confidence_moy` | Fiabilité du signal | Mentions |
| `QuadClass` | Nature de l'événement | Events |
| `EventRootCode` | Type d'action CAMEO | Events |
| `mois` | Saisonnalité | Events |

> `nb_sources_uniques` **exclu** : corrélation de 0.98 avec `nb_mentions` → fuite potentielle.

### Algorithmes testés

#### 1. DBSCAN — Détection d'anomalies et événements atypique


**Ce que DBSCAN révèle :**
- Événements totalement atypiques (outliers = -1) → signaux d'alerte précoce
- Clusters de densité variable → zones de tension localisées
- Pas besoin de spécifier k à l'avance → découverte organique des patterns

#### 2. Spectral Clustering — Relations complexes entre événements

**Ce que Spectral révèle :**
- Relations non-linéaires entre événements (que K-Means ne peut pas capturer)
- Communautés médiatiques partageant des patterns de couverture similaires
- Structure de graphe des événements liés


**Pourquoi GMM est le plus adapté :**
- Fournit une **probabilité d'appartenance** (pas d'assignation dure) → un événement peut appartenir à 60% au cluster "risque" et 40% au cluster "sensible"
- Gère les clusters de **formes elliptiques** non-sphériques (caractéristique des données GDELT)
- Le critère **BIC** sélectionne automatiquement le nombre optimal de clusters
- Idéal pour modéliser des **zones grises** (événements ambigus)

### Profil des 5 clusters identifiés (GMM)

| Cluster | Nom | Goldstein | Ton médias | Viralité | Interprétation |
|---|---|---|---|---|---|
| C0 | Diplomatie stable | +3.2 | -0.8 | Faible | Coopération institutionnelle discrète |
| C1 | Zone de risque | -4.1 | -6.3 | Élevée | Conflits avec forte couverture négative |
| C2 | Tension latente | -1.2 | -2.9 | Moyenne | Conflits verbaux, désaccords diplomatiques |
| C3 | Vitrine internationale | +1.8 | +2.1 | Élevée | Événements positifs très médiatisés |
| C4 | Sensibilité sociale | -0.5 | -4.7 | Très élevée | Sujets viraux avant d'être des crises |

**Insight clé :** Les événements négatifs se propagent en moyenne **3× plus vite** que les événements de coopération positive.

---

## 📈 Résultats des modèles ML

| GMM Clustering (k=5, BIC-optimal) | Silhouette: 0.136 | — | Modèle principal |

> La variable `nb_sources_uniques` avait été exclue du ML supervisé pour éviter une **fuite de données** (corrélation 0.98 avec la cible de viralité).

---

## 🚀 Reproductibilité

### 1. Installation

```bash


git clone https://github.com/dona-eric/Hackaton-Isheero-Equipe-15.git

cd Hackaton-Isheero-Equipe-15

pip install -r requirements.txt

```

### 2. Téléchargement du modèle GMM (Hugging Face)

```python
import joblib
from huggingface_hub import hf_hub_download

# Configurer le token HuggingFace
import os
os.environ["HF_TOKEN"] = "VOTRE_TOKEN_HF"

# Téléchargement du modèle GMM optimisé (BIC k=5)
model_path = hf_hub_download(
    repo_id="donerick/gaussian-model-v1",
    filename="gaussian-model.pkl",
    token=os.environ["HF_TOKEN"]
)

# Chargement et prédiction
model = joblib.load(model_path)
print("✅ Modèle GMM chargé avec succès.")

# Prédire le cluster d'un nouvel événement
# X_new = scaler.transform([[goldstein, tone, nb_mentions, ...]])
# cluster = model.predict(X_new)
# proba   = model.predict_proba(X_new)  # Appartenance probabiliste
```

### 5. Token HuggingFace

```bash
export HF_TOKEN='votre_token_ici'
```

---

## 📋 Bonnes pratiques qualité des données

- **Filtrer `Confidence >= 50`** pour les analyses critiques (42% des mentions ont Confidence < 40)
- **Signaler BENIN CITY** dans tous les livrables (778 occurrences = ville du Nigeria, pas un acteur béninois)
- **Utiliser `ActionGeo_CountryCode`** pour la géographie de l'action, pas `Actor1Geo_*` (lieu de l'acteur ≠ lieu de l'événement)
- **Exclure `NumArticles`** des analyses (corrélation 0.99 avec `NumMentions` → redondant)

---

## 📁 Données et reproducibilité

```
data/
├── raw/

├── processed/

└── exports/                  
```

---

## 🔭 Prochaines étapes

- [ ] **Collecter les données GKG** (thèmes CAMEO, citations, ton article complet)
- [ ] **Enrichir le clustering** avec les thèmes GKG → gain attendu +10-15 pts Silhouette
- [ ] **Construire le dashboard Streamlit** avec carte interactive et alertes automatiques
- [ ] **Affiner DBSCAN** : k-distance graph pour optimiser `eps` sur les vraies données
- [ ] **Comparer les 3 algorithmes** sur les mêmes features → tableau de bord de sélection
- [ ] **Déployer l'API d'alerte précoce** sur les événements du cluster C4 (sensibilité sociale)

---

## 🛠️ Stack technique

| Outil | Usage |
|---|---|
| Python 3.11 | Langage principal |
| pandas · numpy | Manipulation des données |
| scikit-learn | Clustering · ML · évaluation |
| matplotlib · seaborn | Visualisations |
| Google BigQuery | Collecte GDELT à grande échelle |
| Hugging Face Hub | Versionning et partage des modèles |
| POwerBI | Dashboard interactif (phase 3) |
| Parquet (snappy) | Stockage optimisé des données traitées |

---

## 👥 Équipe

| Rôle | Membre | Email |
|---|---|---|
| Data Engineer | Peace Solange ADOKPO | ahouefa05@gmail.com |
| Data Scientist | Mamadou  Diallo| mamadoulamaranadiallomld1@gmail.com |
| ML Engineer | Eric KOULODJI | donaerickoulodji@gmail.com |
| ML Engineer | Sunday KOGBETSE | skogbetse@gmail.com |

---