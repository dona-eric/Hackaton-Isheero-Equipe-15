#!/usr/bin/env python
# ============================================================
# run_pipeline.py
# Point d'entrée unique pour lancer le pipeline complet
# Bénin Insights Challenge · iSHEERO × DataCamp 2026
# ============================================================
"""
Usage
-----
  # Collecte + nettoyage (méthode directe, recommandée sans BigQuery)
  python run_pipeline.py

  # Avec BigQuery (requiert GOOGLE_APPLICATION_CREDENTIALS)
  python run_pipeline.py --method bigquery

  # Recollecte forcée (ignore le cache)
  python run_pipeline.py --force-reload

  # Tester sur les 7 derniers jours seulement
  python run_pipeline.py --days 7
"""

import typer
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import sys
import os
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import setup_logger
from typing import Optional
from src.pipeline.cleaner import GDELTCleaner
from src.pipeline.collector import GDELTCollector
from src.pipeline.loader import GDELTLoader
from config import END_DATE, START_DATE
logger = setup_logger()
app = typer.Typer(help="Pipeline GDELT - HACKATON Isheero")
console = Console()


@app.command()
def run(
    method: str = typer.Option(
        "direct",
        "--method", "-m",
        help="Méthode de collecte : 'direct' ou 'bigquery'",
    ),
    days: Optional[int] = typer.Option(
        None,
        "--days", "-d",
        help="Nombre de jours à collecter (défaut : 365)",
    ),
    force_reload: bool = typer.Option(
        False,
        "--force-reload",
        help="Ignore le cache et re-télécharge tout",
    ),
):
    """Lance le pipeline complet : collecte → nettoyage → sauvegarde."""

    console.print(
        Panel.fit(
            "[bold cyan]HACKATON Isheero[/bold cyan]\n"
            "[dim]Isheero DataCamp 2026[/dim]\n"
            f"[green]Méthode : {method} | Jours : {days or 365} | Force : {force_reload}[/green]",
            title="Pipeline GDELT",
            border_style="cyan",
        )
    )

    # ── 1. Collecte 
    end_date = END_DATE
    start_date = START_DATE

    s_date = datetime.strptime(str(start_date), "%Y%m%d").date()
    e_date = datetime.strptime(str(end_date), "%Y%m%d").date()

    console.print(f"\n[bold] Étape 1/3 — Collecte[/bold]")
    console.print(f"   Période : {s_date} → {e_date}")

    collector = GDELTCollector(start_date=start_date, end_date=end_date)
    df_raw = collector.collect(method=method)

    stats = collector.get_collection_stats(df_raw)
    _print_stats_table(stats, "Statistiques de collecte")

    if df_raw.empty:
        console.print("[bold red] Collecte échouée — pipeline interrompu.[/bold red]")
        raise typer.Exit(1)

    # 2. Nettoyage
    console.print(f"\n[bold] ** Étape 2/3 — Nettoyage[/bold]")

    cleaner  = GDELTCleaner()
    df_clean = cleaner.clean(df_raw, save=True)

    report = cleaner.get_cleaning_report(df_raw, df_clean)
    console.print(
        f"   ✅ {report['lignes_avant']:,} → {report['lignes_apres']:,} lignes "
        f"({report['lignes_supprimees']:,} doublons supprimés)"
    )

    # Résumé final 
    console.print(f"\n[bold] Étape 3/3 — Résumé[/bold]")
    loader = GDELTLoader()
    loader.summary(df_clean)

    console.print(
        Panel.fit(
            "[bold green] Pipeline terminé avec succès ![/bold green]\n"
            "[dim]Données disponibles dans data/processed/benin_events_clean.parquet[/dim]",
            border_style="green",
        )
    )


def _print_stats_table(stats: dict, title: str) -> None:
    """Affiche les statistiques dans un tableau Rich."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Indicateur", style="dim")
    table.add_column("Valeur",     style="green")
    for k, v in stats.items():
        table.add_row(str(k), str(v))
    console.print(table)


if __name__ == "__main__":
    app()