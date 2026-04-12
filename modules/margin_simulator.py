import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List


ELASTICITY_PRESETS = {
    "très élastique (ex: accessoires)": -2.5,
    "élastique (ex: électronique)": -1.8,
    "normal (e-commerce moyen)": -1.3,
    "peu élastique (ex: électroménager premium)": -0.8,
    "inélastique (ex: consommables)": -0.4,
}


@dataclass
class SimulationScenario:
    label: str
    new_price: float
    cost_price: float
    delivery_cost: float
    current_price: float
    current_volume_30d: int
    elasticity: float = -1.3

    def compute(self) -> dict:
        revenue = self.new_price - self.delivery_cost
        margin_euros = revenue - self.cost_price
        margin_rate = margin_euros / revenue if revenue > 0 else 0

        price_change_pct = (self.new_price - self.current_price) / self.current_price
        volume_change_pct = self.elasticity * price_change_pct
        new_volume = max(0, self.current_volume_30d * (1 + volume_change_pct))

        current_revenue = self.current_price - self.delivery_cost
        current_margin = (current_revenue - self.cost_price) * self.current_volume_30d
        new_margin_total = margin_euros * new_volume

        return {
            "label": self.label,
            "new_price": round(self.new_price, 2),
            "margin_euros": round(margin_euros, 2),
            "margin_rate_pct": round(margin_rate * 100, 2),
            "price_change_pct": round(price_change_pct * 100, 2),
            "estimated_volume_30d": round(new_volume),
            "estimated_margin_total": round(new_margin_total, 2),
            "current_margin_total": round(current_margin, 2),
            "margin_impact": round(new_margin_total - current_margin, 2),
            "margin_impact_pct": round((new_margin_total - current_margin) / abs(current_margin) * 100, 2) if current_margin != 0 else 0,
        }


def simulate_scenarios(
    cost_price: float,
    current_price: float,
    delivery_cost: float,
    current_volume: int,
    price_variants: List[float],
    elasticity: float = -1.3,
) -> pd.DataFrame:
    results = []
    for i, price in enumerate(price_variants):
        pct_change = round((price - current_price) / current_price * 100, 1)
        label = f"Scénario {i+1} ({'+' if pct_change >= 0 else ''}{pct_change}%)"
        s = SimulationScenario(
            label=label,
            new_price=price,
            cost_price=cost_price,
            delivery_cost=delivery_cost,
            current_price=current_price,
            current_volume_30d=current_volume,
            elasticity=elasticity,
        )
        results.append(s.compute())

    current_revenue = current_price - delivery_cost
    current_margin_e = current_revenue - cost_price
    current_margin_r = current_margin_e / current_revenue if current_revenue > 0 else 0
    baseline = {
        "label": "Situation actuelle",
        "new_price": round(current_price, 2),
        "margin_euros": round(current_margin_e, 2),
        "margin_rate_pct": round(current_margin_r * 100, 2),
        "price_change_pct": 0.0,
        "estimated_volume_30d": current_volume,
        "estimated_margin_total": round(current_margin_e * current_volume, 2),
        "current_margin_total": round(current_margin_e * current_volume, 2),
        "margin_impact": 0.0,
        "margin_impact_pct": 0.0,
    }

    df = pd.DataFrame([baseline] + results)
    return df


def find_optimal_price(
    cost_price: float,
    current_price: float,
    delivery_cost: float,
    current_volume: int,
    competitor_price: float,
    elasticity: float = -1.3,
    min_margin_rate: float = 0.08,
    steps: int = 20,
) -> dict:
    price_min = cost_price * 1.02
    price_max = max(current_price * 1.3, competitor_price * 1.1)
    prices = np.linspace(price_min, price_max, steps)

    best = None
    best_margin_total = -np.inf

    for p in prices:
        revenue = p - delivery_cost
        if revenue <= 0:
            continue
        margin_e = revenue - cost_price
        margin_r = margin_e / revenue
        if margin_r < min_margin_rate:
            continue
        price_change = (p - current_price) / current_price
        new_vol = max(0, current_volume * (1 + elasticity * price_change))
        total = margin_e * new_vol
        if total > best_margin_total:
            best_margin_total = total
            best = {
                "optimal_price": round(p, 2),
                "optimal_margin_rate_pct": round(margin_r * 100, 2),
                "optimal_margin_euros": round(margin_e, 2),
                "optimal_volume_30d": round(new_vol),
                "optimal_margin_total_30d": round(total, 2),
                "vs_current_price_pct": round((p - current_price) / current_price * 100, 2),
                "vs_competitor_pct": round((p - competitor_price) / competitor_price * 100, 2),
            }

    return best or {}
