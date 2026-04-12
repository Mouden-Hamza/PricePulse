import pandas as pd
import numpy as np


THRESHOLDS = {
    "vs_historical": 0.10,   # >10% écart vs historique
    "vs_competitor": 0.15,   # >15% écart vs concurrent
    "margin_min": 0.05,      # marge brute minimale acceptable
}

SEVERITY_LEVELS = {
    "critique": 3,
    "moyen": 2,
    "faible": 1,
    "normal": 0,
}


def compute_margin(row):
    revenue = row["current_price"] - row["delivery_cost"]
    margin = (revenue - row["cost_price"]) / revenue if revenue > 0 else 0
    return round(margin, 4)


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["margin_rate"] = df.apply(compute_margin, axis=1)
    df["gross_margin_euros"] = round(df["current_price"] - df["delivery_cost"] - df["cost_price"], 2)

    df["gap_vs_historical_pct"] = round(
        (df["current_price"] - df["historical_avg_price"]) / df["historical_avg_price"] * 100, 2
    )
    df["gap_vs_competitor_pct"] = round(
        (df["current_price"] - df["competitor_price"]) / df["competitor_price"] * 100, 2
    )

    df["flag_historical"] = abs(df["gap_vs_historical_pct"]) > THRESHOLDS["vs_historical"] * 100
    df["flag_competitor"] = abs(df["gap_vs_competitor_pct"]) > THRESHOLDS["vs_competitor"] * 100
    df["flag_margin"] = df["margin_rate"] < THRESHOLDS["margin_min"]

    df["anomaly_score"] = (
        df["flag_historical"].astype(int) +
        df["flag_competitor"].astype(int) +
        df["flag_margin"].astype(int)
    )

    def severity(row):
        if row["anomaly_score"] >= 3:
            return "critique"
        elif row["anomaly_score"] == 2:
            return "moyen"
        elif row["anomaly_score"] == 1:
            return "faible"
        return "normal"

    df["severity"] = df.apply(severity, axis=1)
    df["severity_rank"] = df["severity"].map(SEVERITY_LEVELS)

    df["price_direction"] = df["gap_vs_historical_pct"].apply(
        lambda x: "sur-tarification" if x > 0 else ("sous-tarification" if x < 0 else "stable")
    )

    return df


def get_anomaly_summary(df: pd.DataFrame) -> dict:
    flagged = df[df["severity"] != "normal"]
    return {
        "total_products": len(df),
        "total_anomalies": len(flagged),
        "anomaly_rate_pct": round(len(flagged) / len(df) * 100, 1),
        "critique": len(df[df["severity"] == "critique"]),
        "moyen": len(df[df["severity"] == "moyen"]),
        "faible": len(df[df["severity"] == "faible"]),
        "avg_margin_rate": round(df["margin_rate"].mean() * 100, 2),
        "low_margin_count": len(df[df["flag_margin"]]),
        "overpriced_count": len(df[(df["flag_competitor"]) & (df["gap_vs_competitor_pct"] > 0)]),
        "underpriced_count": len(df[(df["flag_competitor"]) & (df["gap_vs_competitor_pct"] < 0)]),
    }
