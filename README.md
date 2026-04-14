# PricePulse

**Outil Python de détection d'anomalies pricing et simulation de marge**  
Conçu pour les équipes pricing e-commerce — inspiré des workflows Cdiscount, Amazon, Fnac.

---

## Problème résolu

Les équipes pricing passent un temps significatif à détecter manuellement les produits dont le prix s'est écarté de la concurrence ou de l'historique. Ce pipeline automatise cette détection, simule l'impact marge de tout changement de prix, et génère un rapport Excel hebdomadaire prêt à présenter.

---

## Fonctionnalités

### Module 1 — Détection d'anomalies (`anomaly_detector.py`)
- Calcul automatique des écarts prix vs historique et vs concurrent
- Scoring de criticité sur 3 niveaux : **Faible / Moyen / Critique**
- Détection des marges sous le seuil minimal configurable
- Identification des produits sur-tarifés et sous-tarifés

### Module 2 — Simulateur de marge (`margin_simulator.py`)
- Simulation multi-scénarios de repricing avec élasticité-prix configurable
- Calcul de l'impact volume et de l'impact marge totale par scénario
- Optimiseur de prix : trouve le prix maximisant la marge totale sous contrainte de marge minimale

### Module 3 — Rapport Excel automatisé (`report_generator.py`)
- 5 onglets structurés : résumé exécutif, anomalies, analyse catégorie, opportunités, catalogue complet
- Code couleur par sévérité, filtres automatiques, mise en forme professionnelle
- Prêt à présenter en réunion hebdomadaire

### Visualisations (`main.py`)
- Dashboard 4 graphiques : anomalies par catégorie, distribution des marges, répartition sévérité, écart concurrent
- Carte pricing : position de chaque produit selon marge vs écart concurrent

---

## Stack technique

| Outil | Usage |
|-------|-------|
| `pandas` | Manipulation et analyse du catalogue (5 000+ références) |
| `numpy` | Calculs vectorisés (marges, élasticités, optimisation) |
| `matplotlib` | Visualisations et dashboard |
| `openpyxl` | Génération du rapport Excel multi-onglets |

---

## Installation & usage

```bash
git clone https://github.com/Mouden-Hamza/pricepulse
cd pricepulse
pip install -r requirements.txt
python main.py
```

Les fichiers générés apparaissent dans le dossier `outputs/` :
- `PricePulse_Rapport_YYYYMMDD.xlsx` — rapport Excel complet
- `dashboard.png` — tableau de bord graphique
- `scatter_pricing_map.png` — carte de positionnement des produits

---

## Structure du projet

```
pricepulse/
├── main.py                    # Pipeline principal
├── data/
│   └── generate_data.py       # Générateur de données simulées
├── modules/
│   ├── anomaly_detector.py    # Détection d'anomalies
│   ├── margin_simulator.py    # Simulation de marge & optimiseur
│   └── report_generator.py   # Génération rapport Excel
├── outputs/                   # Fichiers générés
└── README.md
```

---

## Paramètres configurables

Dans `anomaly_detector.py` :
```python
THRESHOLDS = {
    "vs_historical": 0.10,   # Seuil écart vs historique (10%)
    "vs_competitor": 0.15,   # Seuil écart vs concurrent (15%)
    "margin_min": 0.05,      # Marge minimale acceptable (5%)
}
```

Dans `margin_simulator.py` :
```python
ELASTICITY_PRESETS = {
    "très élastique (ex: accessoires)": -2.5,
    "élastique (ex: électronique)": -1.8,
    "normal (e-commerce moyen)": -1.3,
    "peu élastique (ex: électroménager premium)": -0.8,
}
```

---

## Auteur

**Mouden Hamza** — Étudiant M2 Finance, Brest Business School  
Projet réalisé dans le cadre d'une candidature alternance Business Analyst Pricing.
