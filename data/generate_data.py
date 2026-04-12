import pandas as pd
import numpy as np

np.random.seed(42)

CATEGORIES = ["Informatique", "Téléphonie", "Electroménager", "Jeux vidéo", "Maison", "Sport", "Beauté", "Jouets"]

N = 5000

product_ids = [f"PRD{str(i).zfill(5)}" for i in range(1, N+1)]
categories = np.random.choice(CATEGORIES, N)
cost_prices = np.round(np.random.uniform(5, 800, N), 2)
margin_targets = np.random.uniform(0.10, 0.45, N)
base_prices = np.round(cost_prices * (1 + margin_targets), 2)

# Current prices: mostly normal, ~15% with anomalies
current_prices = base_prices.copy()
anomaly_mask = np.random.random(N) < 0.15
anomaly_direction = np.random.choice([-1, 1], N)
anomaly_magnitude = np.random.uniform(0.15, 0.50, N)
current_prices[anomaly_mask] = np.round(
    base_prices[anomaly_mask] * (1 + anomaly_direction[anomaly_mask] * anomaly_magnitude[anomaly_mask]), 2
)
current_prices = np.maximum(current_prices, 0.99)

# Competitor prices
competitor_prices = np.round(base_prices * np.random.uniform(0.85, 1.20, N), 2)

# Delivery costs
delivery_costs = np.where(current_prices > 50, 0, np.round(np.random.uniform(2.99, 6.99, N), 2))

# Sales volume (last 30 days)
sales_volume = np.random.randint(0, 500, N)

# Historical avg price (last 90 days)
historical_avg = np.round(base_prices * np.random.uniform(0.95, 1.05, N), 2)

df = pd.DataFrame({
    "product_id": product_ids,
    "product_name": [f"Produit {cat[:3].upper()}-{pid[-4:]}" for cat, pid in zip(categories, product_ids)],
    "category": categories,
    "cost_price": cost_prices,
    "current_price": current_prices,
    "competitor_price": competitor_prices,
    "historical_avg_price": historical_avg,
    "delivery_cost": delivery_costs,
    "sales_volume_30d": sales_volume,
})

df.to_csv("Desktop\PricePulseProjet/home/center/pricepulse/data/catalog.csv", index=False)
print(f"Catalogue généré : {N} produits, {anomaly_mask.sum()} anomalies simulées ({anomaly_mask.mean()*100:.1f}%)")
