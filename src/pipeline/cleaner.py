# src/pipeline/cleaner.py

from pathlib import Path
import numpy as np
import pandas as pd
from config import setup_logger

import sys
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    GDELT_COLUMNS,
    GDELT_DTYPES,
    QUAD_CLASS_LABELS,
    CAMEO_ROOT_LABELS,
    PROCESSED_DIR
)

logger = setup_logger()

class GDELTCleaner:
    """
    Nettoyeur haute performance pour GDELT Bénin.
    Optimisé pour les types de données MLOps et la mémoire.
    """

    LAT_RANGE = (-90.0, 90.0)
    LON_RANGE = (-180.0, 180.0)

    def __init__(self, processed_dir: Path = PROCESSED_DIR):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def clean(self, df: pd.DataFrame, save: bool = True, filename: str = "benin_events_clean.parquet") -> pd.DataFrame:
        if df.empty:
            logger.warning("DataFrame vide reçu pour le nettoyage.")
            return df

        logger.info(f"Nettoyage de {len(df):,} lignes...")

        # Pipeline de transformation
        df = (
            df.pipe(self._align_columns)
              .pipe(self._convert_types)
              .pipe(self._parse_dates)
              .pipe(self._remove_duplicates)
              .pipe(self._handle_missing)
              .pipe(self._validate_coordinates)
              .pipe(self._add_labels)
              .pipe(self._add_derived_features)
        )

        if save:
            # Utilisation de zstd pour un meilleur ratio compression/vitesse
            out_path = self.processed_dir / filename
            df.to_parquet(out_path, index=False, compression="zstd")
            logger.info(f"💾 Dataset propre sauvegardé : {out_path}")

        return df

    def _align_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # S'assurer que les colonnes essentielles sont présentes
        missing_cols = set(GDELT_COLUMNS) - set(df.columns)
        for col in missing_cols:
            df[col] = np.nan
        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Utilise les types Nullable de Pandas pour plus de robustesse."""
        for col, dtype in GDELT_DTYPES.items():
            if col in df.columns:
                # On convertit d'abord en numérique (float pour gérer les NaNs temporaires)
                df[col] = pd.to_numeric(df[col], errors="coerce")
                # Puis on caste vers le type cible (Int64 pour les entiers supportant les NaNs)
                target_type = "Int64" if "int" in dtype.lower() else "float32"
                df[col] = df[col].astype(target_type)
        return df

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        # Conversion rapide
        df["date"] = pd.to_datetime(df["Day"].astype(str), format="%Y%m%d", errors="coerce")
        # Ajout de features temporelles cycliques (utile pour le ML)
        df["month"] = df["date"].dt.month.astype("Int8")
        df["day_of_week_num"] = df["date"].dt.dayofweek.astype("Int8")
        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.drop_duplicates(subset=["GlobalEventID"], keep="first")

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        # Imputation intelligente
        if "GoldsteinScale" in df.columns:
            df["GoldsteinScale"] = df["GoldsteinScale"].fillna(0.0)
        
        if "AvgTone" in df.columns:
            # Médiane par mois pour être plus précis
            df["AvgTone"] = df.groupby("month")["AvgTone"].transform(lambda x: x.fillna(x.median()))
            # Si encore des NaNs (mois vides), médiane globale
            df["AvgTone"] = df["AvgTone"].fillna(df["AvgTone"].median())
        return df

    def _validate_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        # On utilise une approche vectorisée rapide
        mask_lat = df["ActionGeo_Lat"].between(*self.LAT_RANGE) | df["ActionGeo_Lat"].isna()
        mask_lon = df["ActionGeo_Long"].between(*self.LON_RANGE) | df["ActionGeo_Long"].isna()
        df.loc[~mask_lat, "ActionGeo_Lat"] = np.nan
        df.loc[~mask_lon, "ActionGeo_Long"] = np.nan
        return df

    def _add_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        # Mapping depuis config.py
        if "QuadClass" in df.columns:
            df["QuadClass_label"] = df["QuadClass"].astype(str).map(QUAD_CLASS_LABELS)
        
        if "EventRootCode" in df.columns:
            # Assurer que le code est sur 2 caractères (ex: '1' -> '01')
            df["EventRootCode_str"] = df["EventRootCode"].astype(str).str.zfill(2)
            df["EventRootCode_label"] = df["EventRootCode_str"].map(CAMEO_ROOT_LABELS)
        return df

    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
            score_impact_event: est une feature qui evalue l'impact en 
            multipliant le nombre d'articles par la valeur absolue du 
            score de Goldstein permet d'identifier tout de suite les 
            événements qui ont "fait du bruit" et qui ont un poids politique fort
        """
        # Score d'impact
        if "NumArticles" in df.columns and "GoldsteinScale" in df.columns:
            df["event_impact_score"] = (df["NumArticles"] * df["GoldsteinScale"].abs()).round(2)
        
        # Flag de conflit
        df["is_conflict"] = (df["QuadClass"] >= 3).astype("int8")
        return df

    def get_cleaning_report(self, df_raw: pd.DataFrame, df_clean: pd.DataFrame) -> dict:
        """Retourne le rapport de nettoyage."""
        if df_raw is None or df_clean is None:
            return {"lignes_avant": 0, "lignes_apres": 0, "lignes_supprimees": 0}
        return {
            "lignes_avant": len(df_raw),
            "lignes_apres": len(df_clean),
            "lignes_supprimees": len(df_raw) - len(df_clean)
        }