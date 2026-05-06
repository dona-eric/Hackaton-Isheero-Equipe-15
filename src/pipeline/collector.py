# src/pipeline/collector.py

import io
import time
import zipfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional
import pandas as pd
import requests
from tqdm import tqdm
from google.cloud import bigquery
import sys
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from dotenv import load_dotenv
from config import (START_DATE, END_DATE, setup_logger, QUAD_CLASS_LABELS, 
                    GDELT_BASE_URL, GDELT_COLUMNS, BENIN_COUNTRY_CODE,
                    RAW_DIR, BQ_PROJECT)


load_dotenv()
logger = setup_logger()

class GDELTCollector:
    """
    Collecteur haute performance pour GDELT. 
    Optimisé pour les extractions 'Bulk' (2025-2026) et le stockage froid.
    """

    def __init__(self, 
                 country_code: str = BENIN_COUNTRY_CODE,
                 start_date: str = "20250101", 
                 end_date: str = "20260101",
                 raw_dir: Path = RAW_DIR):
        
        self.country_code = country_code
        self.start_date = start_date
        self.end_date = end_date
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f" GDELTCollector prêt | Période: {start_date} -> {end_date}")

    def collect(self, method: Literal["direct", "bigquery"] = "bigquery") -> pd.DataFrame:
        """Point d'entrée unique pour la collecte."""
        if method == "bigquery":
            return self._collect_bulk_bigquery()
        return self._collect_direct_optimized()

    def _collect_bulk_bigquery(self) -> pd.DataFrame:
        """
        Extraction via BigQuery. 
        Colonnes limitées pour optimiser les coûts et la vitesse.
        """
        logger.info(f" Requête BigQuery en cours pour le pays: {self.country_code}...")

        # On évite SELECT * pour réduire le scan de données ($$)
        # On se concentre sur l'essentiel pour le ML
        query = f"""
        SELECT *
        
        FROM `gdelt-bq.gdeltv2.events`
        WHERE SQLDATE BETWEEN {self.start_date} AND {self.end_date}
          AND (
              ActionGeo_CountryCode = '{self.country_code}'
              OR Actor1CountryCode = '{self.country_code}'
              OR Actor2CountryCode = '{self.country_code}'
          )
        ORDER BY SQLDATE ASC
        """

        client = bigquery.Client(
            project=BQ_PROJECT)
        try:
            query_job = client.query(query)
            df = query_job.to_dataframe()
            
            output_path = self.raw_dir / f"gdelt_benin_bulk_{self.start_date}_{self.end_date}.parquet"
            df.to_parquet(output_path, compression='snappy')
            
            logger.info(f" {len(df)} événements extraits et sauvegardés sous {output_path}")
            return df
        except Exception as e:
            logger.error(f" Erreur BigQuery: {e}")
            return pd.DataFrame()

    def _collect_direct_optimized(self) -> pd.DataFrame:
        """
        Version optimisée du téléchargement direct. 
        Sauvegarde chaque jour en Parquet pour éviter la saturation RAM.
        """
        start = datetime.strptime(self.start_date, "%Y%m%d")
        end = datetime.strptime(self.end_date, "%Y%m%d")
        
        current = start
        all_dfs = []

        logger.info("Début du téléchargement direct CSV")

        while current <= end:
            date_str = current.strftime("%Y%m%d")
            url = f"{GDELT_BASE_URL}/{date_str}.export.CSV.zip"
            
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                        with zf.open(zf.namelist()[0]) as f:
                            df_day = pd.read_csv(f, sep="\t", header=None, names=GDELT_COLUMNS, 
                                                 dtype=str, usecols=range(len(GDELT_COLUMNS)))
                            
                            # Filtrage immédiat pour ne pas garder 100MB en RAM inutilement
                            df_filtered = df_day[
                                (df_day["ActionGeo_CountryCode"] == self.country_code) |
                                (df_day["Actor1CountryCode"] == self.country_code)
                            ].copy()
                            
                            if not df_filtered.empty:
                                all_dfs.append(df_filtered)
                
                current += timedelta(days=1)
                
            except Exception as e:
                logger.warning(f" Erreur pour le {date_str}: {e}")
                current += timedelta(days=1)

        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"Collecte directe terminée: {len(final_df)} lignes.")
            return final_df
        
        return pd.DataFrame()

    def get_collection_stats(self, df: pd.DataFrame) -> dict:
        """Retourne les statistiques de la collecte."""
        if df is None or df.empty:
            return {"Statut": "Vide", "Lignes": 0}
        return {
            "Lignes extraites": len(df),
            "Pays": self.country_code,
            "Taille en mémoire (MB)": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }