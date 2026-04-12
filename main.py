"""
PricePulse — Pipeline principal
Auteur : Mouden Hamza
Description : Outil de détection d'anomalies pricing et simulation de marge
              conçu pour les équipes pricing e-commerce.
Usage : python main.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime

from modules.anomaly_detector import detect_anomalies, get_anomaly_summary
from modules.margin_simulator import simulate_scenarios, find_optimal_price, ELASTICITY_PRESETS
from modules.report_generator import build_report


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run_pipeline():
    print_section("PRICEPULSE — DÉMARRAGE DU PIPELINE")
    print(f"  Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    print_section("ÉTAPE 1 — Génération des données simulées")
    exec(open(os.path.join(os.path.dirname(__file__), "data/generate_data.py")).read())

    print_section("ÉTAPE 2 — Chargement du catalogue")
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "data/catalog.csv"))
    print(f"  {len(df):,} produits chargés | {df['category'].nunique()} catégories")

    print_section("ÉTAPE 3 — Détection des anomalies")
    df_analyzed = detect_anomalies(df)
    summary = get_anomaly_summary(df_analyzed)

    print(f"  Anomalies détectées : {summary['total_anomalies']:,} ({summary['anomaly_rate_pct']}%)")
    print(f"  - Critiques : {summary['critique']}")
    print(f"  - Moyennes  : {summary['moyen']}")
    print(f"  - Faibles   : {summary['faible']}")
    print(f"  Marge moyenne catalogue : {summary['avg_margin_rate']}%")
    print(f"  Produits sur-tarifés    : {summary['overpriced_count']}")
    print(f"  Produits sous-tarifés   : {summary['underpriced_count']}")

    print_section("ÉTAPE 4 — Simulation de marge (exemple sur 1 produit)")
    sample = df_analyzed[df_analyzed["severity"] == "critique"].iloc[0]
    print(f"\n  Produit : {sample['product_name']} ({sample['product_id']})")
    print(f"  Prix actuel       : {sample['current_price']} €")
    print(f"  Prix concurrent   : {sample['competitor_price']} €")
    print(f"  Coût d'achat      : {sample['cost_price']} €")
    print(f"  Marge actuelle    : {round(sample['margin_rate']*100, 1)}%")

    competitor_ref = sample["competitor_price"]
    price_variants = [
        round(sample["current_price"] * 0.90, 2),
        round(competitor_ref * 0.98, 2),
        round(competitor_ref, 2),
        round(competitor_ref * 1.02, 2),
        round(sample["current_price"] * 1.10, 2),
    ]

    sim_df = simulate_scenarios(
        cost_price=sample["cost_price"],
        current_price=sample["current_price"],
        delivery_cost=sample["delivery_cost"],
        current_volume=max(1, sample["sales_volume_30d"]),
        price_variants=price_variants,
        elasticity=-1.3,
    )

    print("\n  Résultats de simulation :")
    print(f"  {'Scénario':<30} {'Prix (€)':>10} {'Marge (%)':>10} {'Volume':>8} {'Marge totale (€)':>16} {'Impact (€)':>12}")
    print(f"  {'-'*90}")
    for _, row in sim_df.iterrows():
        impact_str = f"{'+' if row['margin_impact'] >= 0 else ''}{row['margin_impact']:.0f}"
        print(f"  {row['label']:<30} {row['new_price']:>10.2f} {row['margin_rate_pct']:>9.1f}% "
              f"{row['estimated_volume_30d']:>8} {row['estimated_margin_total']:>16.0f} {impact_str:>12}")

    optimal = find_optimal_price(
        cost_price=sample["cost_price"],
        current_price=sample["current_price"],
        delivery_cost=sample["delivery_cost"],
        current_volume=max(1, sample["sales_volume_30d"]),
        competitor_price=sample["competitor_price"],
        elasticity=-1.3,
    )
    if optimal:
        print(f"\n  Prix optimal calculé : {optimal['optimal_price']} € "
              f"(marge {optimal['optimal_margin_rate_pct']}%, "
              f"impact marge totale : {optimal['optimal_margin_total_30d']:.0f} €)")

    print_section("ÉTAPE 5 — Génération des visualisations")
    _generate_charts(df_analyzed, summary)

    print_section("ÉTAPE 6 — Génération du rapport Excel")
    report_path = os.path.join(OUTPUT_DIR, f"PricePulse_Rapport_{datetime.now().strftime('%Y%m%d')}.xlsx")
    build_report(df_analyzed, summary, report_path)

    print_section("PIPELINE TERMINÉ")
    print(f"  Rapport Excel   : {report_path}")
    print(f"  Visualisations  : {OUTPUT_DIR}/")
    print(f"  Durée totale    : pipeline complet en quelques secondes\n")


def _generate_charts(df, summary):
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "#f8f9fa",
        "axes.grid": True,
        "grid.alpha": 0.4,
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("PricePulse — Tableau de bord hebdomadaire", fontsize=16, fontweight="bold", y=0.98)

    # 1 - Anomalies par catégorie
    ax1 = axes[0, 0]
    cat_anom = df.groupby("category").apply(
        lambda x: pd.Series({
            "critique": (x["severity"] == "critique").sum(),
            "moyen": (x["severity"] == "moyen").sum(),
            "faible": (x["severity"] == "faible").sum(),
        })
    ).sort_values("critique", ascending=True)

    colors_bar = ["#3498db", "#f39c12", "#e74c3c"]
    cat_anom.plot(kind="barh", stacked=True, ax=ax1,
                  color=colors_bar, width=0.7)
    ax1.set_title("Anomalies par catégorie", fontweight="bold")
    ax1.set_xlabel("Nombre d'anomalies")
    ax1.legend(["Faible", "Moyen", "Critique"], loc="lower right")
    ax1.set_ylabel("")

    # 2 - Distribution des marges
    ax2 = axes[0, 1]
    margins = df["margin_rate"] * 100
    ax2.hist(margins, bins=40, color="#0f3460", alpha=0.8, edgecolor="white")
    ax2.axvline(x=5, color="#e74c3c", linestyle="--", linewidth=2, label="Seuil minimum (5%)")
    ax2.axvline(x=margins.mean(), color="#2ecc71", linestyle="--", linewidth=2,
                label=f"Moyenne ({margins.mean():.1f}%)")
    ax2.set_title("Distribution des taux de marge", fontweight="bold")
    ax2.set_xlabel("Taux de marge (%)")
    ax2.set_ylabel("Nombre de produits")
    ax2.legend()

    # 3 - Répartition sévérité (donut)
    ax3 = axes[1, 0]
    sev_counts = df[df["severity"] != "normal"]["severity"].value_counts()
    sev_order = [s for s in ["critique", "moyen", "faible"] if s in sev_counts.index]
    sev_values = [sev_counts[s] for s in sev_order]
    sev_colors_pie = {"critique": "#e74c3c", "moyen": "#f39c12", "faible": "#3498db"}
    colors_pie = [sev_colors_pie[s] for s in sev_order]

    wedges, texts, autotexts = ax3.pie(
        sev_values, labels=[s.capitalize() for s in sev_order],
        colors=colors_pie, autopct="%1.1f%%", startangle=90,
        wedgeprops=dict(width=0.6), pctdistance=0.75
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("white")
        at.set_fontweight("bold")
    ax3.set_title("Répartition par sévérité", fontweight="bold")

    # 4 - Écart prix vs concurrent par catégorie
    ax4 = axes[1, 1]
    cat_gap = df.groupby("category")["gap_vs_competitor_pct"].agg(["mean", "std"]).sort_values("mean")
    bar_colors = ["#e74c3c" if v > 5 else "#2ecc71" if v < -5 else "#95a5a6"
                  for v in cat_gap["mean"]]
    bars = ax4.barh(cat_gap.index, cat_gap["mean"], color=bar_colors, alpha=0.85, height=0.6)
    ax4.axvline(x=0, color="black", linewidth=1)
    ax4.axvline(x=15, color="#e74c3c", linestyle="--", linewidth=1, alpha=0.6, label="Seuil sur-tarification")
    ax4.axvline(x=-15, color="#2ecc71", linestyle="--", linewidth=1, alpha=0.6, label="Seuil sous-tarification")
    ax4.set_title("Écart moyen prix vs concurrent (%)", fontweight="bold")
    ax4.set_xlabel("Écart (%)")
    ax4.legend(fontsize=8)

    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "dashboard.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Dashboard généré : {chart_path}")

    fig2, ax = plt.subplots(figsize=(14, 6))
    sample_data = df.sample(min(300, len(df)), random_state=42)
    scatter_colors = {
        "critique": "#e74c3c", "moyen": "#f39c12",
        "faible": "#3498db", "normal": "#bdc3c7"
    }
    for sev in ["normal", "faible", "moyen", "critique"]:
        mask = sample_data["severity"] == sev
        ax.scatter(
            sample_data[mask]["gap_vs_competitor_pct"],
            sample_data[mask]["margin_rate"] * 100,
            c=scatter_colors[sev], label=sev.capitalize(),
            alpha=0.6, s=40, edgecolors="white", linewidth=0.5
        )
    ax.axhline(y=5, color="#e74c3c", linestyle="--", linewidth=1.5, alpha=0.7, label="Marge min. (5%)")
    ax.axvline(x=0, color="gray", linestyle="-", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Écart vs concurrent (%)", fontsize=12)
    ax.set_ylabel("Taux de marge (%)", fontsize=12)
    ax.set_title("Carte des produits — Marge vs écart concurrent", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    plt.tight_layout()
    scatter_path = os.path.join(OUTPUT_DIR, "scatter_pricing_map.png")
    plt.savefig(scatter_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Carte pricing générée : {scatter_path}")


if __name__ == "__main__":
    run_pipeline()
