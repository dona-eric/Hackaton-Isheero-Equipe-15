# ============================================================
# src/pipeline/loader.py
# Chargement et accès aux données traitées
# ============================================================

from pathlib import Path
from typing import Optional, Union
import pandas as pd
from config import setup_logger

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import PROCESSED_DIR, EXPORTS_DIR

logger = setup_logger()
class GDELTLoader:
    """
    Charge les données GDELT Bénin depuis le répertoire processed/.
    Supporte les formats Parquet (recommandé) et CSV.
    """

    def __init__(
        self,
        processed_dir: Path = PROCESSED_DIR,
        exports_dir: Path   = EXPORTS_DIR,
    ):
        self.processed_dir = processed_dir
        self.exports_dir   = exports_dir

    def load(
        self,
        filename: str = "benin_events_clean.parquet",
        filters: Optional[dict] = None,
    ) -> pd.DataFrame:
        """
        Charge le fichier principal des données nettoyées.

        Params
        filename : Nom du fichier dans processed/
        filters  : Dict de filtres optionnels, ex :
                   {"QuadClass": [3, 4], "Year": [2025]}

        Returns
        
        pd.DataFrame prêt pour l'analyse
        """
        path = self.processed_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier non trouvé : {path}\n"
                "Lancer d'abord le pipeline de collecte."
            )

        logger.info(f"Chargement : {path}")
        if filename.endswith(".parquet"):
            df = pd.read_parquet(path)
        elif filename.endswith(".csv"):
            df = pd.read_csv(path, low_memory=False)
        else:
            raise ValueError(f"Format non supporté : {filename}")

        logger.info(f"{len(df):,} événements chargés")

        if filters:
            df = self._apply_filters(df, filters)
            logger.info(f"{len(df):,} événements après filtrage")

        return df

    def _apply_filters(self, df: pd.DataFrame, filters: dict) -> pd.DataFrame:
        """Applique des filtres sous forme de dict {colonne: valeurs}."""
        for col, values in filters.items():
            if col not in df.columns:
                logger.warning(f"Colonne inconnue ignorée : {col}")
                continue
            if isinstance(values, (list, tuple)):
                df = df[df[col].isin(values)]
            else:
                df = df[df[col] == values]
        return df

    def load_by_period(
        self,
        start: str,
        end: str,
        filename: str = "benin_events_clean.parquet",
    ) -> pd.DataFrame:
        """
        Charge et filtre par période (format 'YYYY-MM-DD').
        """

        df = self.load(filename)
        if "date" not in df.columns:
            raise KeyError("Colonne 'date' absente — relancer le nettoyage.")
        mask = (df["date"] >= start) & (df["date"] <= end)
        return df[mask].copy()

    def export_csv(
        self,
        df: pd.DataFrame,
        filename: str = "benin_events_export.csv",
        encoding: str = "utf-8-sig",
    ) -> Path:
        """Exporte un DataFrame en CSV dans exports/."""
        out = self.exports_dir / filename
        df.to_csv(out, index=False, encoding=encoding)
        logger.info(f"Export CSV : {out} ({len(df):,} lignes)")
        return out

    def export_excel(
        self,
        df: pd.DataFrame,
        filename: str = "benin_events_export.xlsx",
        sheet_name: str = "Bénin GDELT",
    ) -> Path:
        """Exporte un DataFrame en Excel dans exports/."""
        out = self.exports_dir / filename
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        logger.info(f"Export Excel : {out}")
        return out

    def summary(self, df: pd.DataFrame) -> None:
        """Affiche un résumé rapide du DataFrame."""
        print(f"\n{'='*50}")
        print(f"  BÉNIN GDELT — Résumé des données")
        print(f"{'='*50}")
        print(f"  Événements  : {len(df):,}")
        if "date" in df.columns:
            print(f"  Période     : {df['date'].min().date()} → {df['date'].max().date()}")
        if "QuadClass_label" in df.columns:
            print(f"\n  Distribution par type :")
            print(df["QuadClass_label"].value_counts().to_string())
        if "GoldsteinScale" in df.columns:
            print(f"\n  Score Goldstein moyen : {df['GoldsteinScale'].mean():.2f}")
        if "AvgTone" in df.columns:
            print(f"  Tonalité moyenne      : {df['AvgTone'].mean():.2f}")
        print(f"{'='*50}\n")